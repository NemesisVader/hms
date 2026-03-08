<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const departments = ref([]);
const todayStr = new Date().toISOString().split('T')[0];
const doctors = ref([]);
const upcomingAppts = ref([]);
const nextVisits = ref([]);
const loading = ref(true);

const selectedDept = ref(null);
const loadingDoctors = ref(false);

const showBookModal = ref(false);
const bookForm = ref({ doctor_id: null, doctor_name: "", date: "", time: "" });
const bookError = ref("");
const doctorAvailability = ref({});
const doctorBookedSlots = ref({});

// Doctor search
const searchQuery = ref("");
const searchResults = ref([]);
const searchLoading = ref(false);
let searchTimeout = null;

const searchDoctors = () => {
  clearTimeout(searchTimeout);
  if (!searchQuery.value.trim()) {
    searchResults.value = [];
    return;
  }
  searchLoading.value = true;
  searchTimeout = setTimeout(async () => {
    try {
      const res = await api.get("/patient/doctors/search", { params: { q: searchQuery.value.trim() } });
      searchResults.value = res.data;
    } catch (e) { console.error(e); }
    finally { searchLoading.value = false; }
  }, 300);
};

const badgeClass = (status) => {
  if (status === "Booked") return "badge-status badge-booked";
  if (status === "Completed") return "badge-status badge-completed";
  if (status === "Cancelled") return "badge-status badge-cancelled";
  return "badge bg-secondary";
};

const getNext7Days = () => {
  const days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const result = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date();
    d.setDate(d.getDate() + i);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    result.push({
      day: days[d.getDay()],
      dateStr: `${d.getFullYear()}-${mm}-${dd}`,
      label: `${days[d.getDay()]} ${dd}/${mm}`,
    });
  }
  return result;
};

onMounted(async () => {
  try {
    const [deptRes, apptRes, nvRes] = await Promise.allSettled([
      api.get("/patient/departments"),
      api.get("/patient/appointments/upcoming"),
      api.get("/patient/next-visits"),
    ]);

    if (deptRes.status === "fulfilled") departments.value = deptRes.value.data;
    else console.error("[Dashboard] /patient/departments failed:", deptRes.reason);

    if (apptRes.status === "fulfilled") upcomingAppts.value = apptRes.value.data;
    else console.error("[Dashboard] /patient/appointments/upcoming failed:", apptRes.reason);

    if (nvRes.status === "fulfilled") nextVisits.value = nvRes.value.data;
    else console.error("[Dashboard] /patient/next-visits failed:", nvRes.reason);

  } finally {
    loading.value = false;
  }
});

const selectDept = async (dept) => {
  selectedDept.value = dept;
  loadingDoctors.value = true;
  try {
    const res = await api.get("/patient/departments/" + dept.id + "/doctors");
    doctors.value = res.data;
  } catch (e) { console.error(e); }
  finally { loadingDoctors.value = false; }
};

const openBook = async (doc) => {
  bookForm.value = { doctor_id: doc.doctor_id, doctor_name: doc.name, date: "", time: "" };
  bookError.value = "";
  // If availability not provided (e.g. from follow-up reminders), fetch it
  if (doc.availability && Object.keys(doc.availability).length > 0) {
    doctorAvailability.value = doc.availability;
    doctorBookedSlots.value = doc.booked_slots || {};
  } else {
    try {
      const res = await api.get("/patient/doctors/" + doc.doctor_id + "/availability");
      doctorAvailability.value = res.data.availability || {};
      doctorBookedSlots.value = res.data.booked_slots || {};
    } catch { doctorAvailability.value = {}; doctorBookedSlots.value = {}; }
  }
  showBookModal.value = true;
};

const bookAppointment = async () => {
  bookError.value = "";
  if (!bookForm.value.date) {
    bookError.value = "Please select a date";
    return;
  }
  if (allSlotsForDay().length === 0) {
    bookError.value = "Doctor is on leave on the selected day. Please pick another date.";
    return;
  }
  if (!bookForm.value.time) {
    bookError.value = "Please select a time slot";
    return;
  }
  try {
    await api.post("/patient/appointments", {
      doctor_id: bookForm.value.doctor_id,
      date: bookForm.value.date,
      time: bookForm.value.time,
    });
    showBookModal.value = false;
    // Refresh both lists so the reminder banner vanishes without a reload
    const [apptRes, nvRes] = await Promise.allSettled([
      api.get("/patient/appointments/upcoming"),
      api.get("/patient/next-visits"),
    ]);
    if (apptRes.status === "fulfilled") upcomingAppts.value = apptRes.value.data;
    if (nvRes.status === "fulfilled") nextVisits.value = nvRes.value.data;
  } catch (e) {
    bookError.value = e.response?.data?.msg || "Booking failed";
  }
};

const allSlotsForDay = () => {
  if (!bookForm.value.date || !doctorAvailability.value) return [];
  try {
    // Parse as local date (avoid UTC midnight → wrong day in IST)
    const [y, m, d] = bookForm.value.date.split("-").map(Number);
    const dt = new Date(y, m - 1, d);
    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const dayName = dayNames[dt.getDay()];
    return doctorAvailability.value[dayName] || [];
  } catch { return []; }
};

const isSlotBooked = (dateStr, time) => {
  const booked = doctorBookedSlots.value[dateStr] || [];
  return booked.includes(time);
};

const availableSlots = () => {
  return allSlotsForDay().filter(t => !isSlotBooked(bookForm.value.date, t));
};
</script>

<template>
  <div>
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Follow-up Reminders -->
      <div v-if="nextVisits.length > 0" class="card mb-4 border-warning">
        <div class="card-body">
          <h6 class="fw-bold mb-3" style="color:#e67e22">⏰ Follow-up Visit Reminders</h6>
          <div v-for="nv in nextVisits" :key="nv.next_visit + nv.doctor_id">
            <!-- Pending follow-up reminder -->
            <div class="alert alert-warning d-flex justify-content-between align-items-center mb-2 py-2">
              <div style="font-size:0.85rem">
                <strong>{{ nv.next_visit }}</strong> — Dr. {{ nv.doctor_name }} ({{ nv.specialization }})
                <div class="text-muted" style="font-size:0.78rem">Previous diagnosis: {{ nv.diagnosis }}</div>
              </div>
              <button class="btn btn-sm btn-outline-warning" @click="openBook({ doctor_id: nv.doctor_id, name: nv.doctor_name, availability: {} })">
                Book Follow-up
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Upcoming Appointments -->
      <div v-if="upcomingAppts.length > 0" class="card mb-4">
        <div class="card-body">
          <h6 class="fw-bold mb-3">Upcoming Appointments</h6>
          <table class="table table-hover mb-0">
            <thead>
              <tr><th>Doctor</th><th>Date</th><th>Time</th><th>Status</th></tr>
            </thead>
            <tbody>
              <tr v-for="a in upcomingAppts" :key="a.appointment_id">
                <td class="fw-semibold">Dr. {{ a.doctor_name }}</td>
                <td>{{ a.date }}</td>
                <td>{{ a.time }}</td>
                <td><span :class="badgeClass(a.status)">{{ a.status }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Search Doctors -->
      <div class="card mb-4">
        <div class="card-body">
          <h6 class="fw-bold mb-3">Search Doctors</h6>
          <input
            v-model="searchQuery"
            class="form-control mb-3"
            placeholder="Search by doctor name or specialization..."
            @input="searchDoctors"
          />
          <div v-if="searchLoading" class="text-center py-2">
            <div class="spinner-border spinner-border-sm text-primary"></div>
          </div>
          <div v-else-if="searchQuery && searchResults.length === 0" class="text-muted" style="font-size:0.85rem">No doctors found.</div>
          <div v-else-if="searchResults.length > 0" class="row g-3">
            <div v-for="doc in searchResults" :key="doc.doctor_id" class="col-md-6 col-lg-4">
              <div class="doc-card h-100">
                <div class="doc-card-accent"></div>
                <div class="doc-card-body">
                  <div class="doc-card-header">
                    <div class="doc-avatar">{{ doc.name ? doc.name.charAt(0).toUpperCase() : '?' }}</div>
                    <div>
                      <h6>Dr. {{ doc.name }}</h6>
                      <p class="doc-spec">{{ doc.specialization }}</p>
                    </div>
                  </div>
                  <span v-if="doc.department" class="badge bg-light text-dark border mb-2" style="font-size:0.72rem">{{ doc.department }}</span>
                  <div v-if="doc.availability && Object.keys(doc.availability).length">
                    <div class="avail-section-label">Availability</div>
                    <table class="avail-table">
                      <tr v-for="(times, day) in doc.availability" :key="day">
                        <td class="avail-day-label">{{ day }}</td>
                        <td>
                          <div class="avail-slots">
                            <span v-for="t in times" :key="t" class="avail-slot">{{ t }}</span>
                          </div>
                        </td>
                      </tr>
                    </table>
                  </div>
                  <button class="btn-book" @click="openBook(doc)">Book Appointment</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Departments -->
      <h6 class="fw-bold mb-3">Browse Departments</h6>
      <div class="row g-3 mb-4">
        <div v-for="dept in departments" :key="dept.id" class="col-md-4 col-lg-3">
          <div
            class="card h-100"
            :class="{ 'border-primary': selectedDept && selectedDept.id === dept.id }"
            style="cursor:pointer"
            @click="selectDept(dept)"
          >
            <div class="card-body text-center py-3">
              <h6 class="fw-bold mb-1" style="font-size:0.9rem">{{ dept.name }}</h6>
              <span class="badge bg-light text-dark border" style="font-size:0.75rem">{{ dept.doctor_count }} Doctors</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Doctors -->
      <div v-if="selectedDept">
        <h6 class="fw-bold mb-3">Doctors in {{ selectedDept.name }}</h6>

        <div v-if="loadingDoctors" class="loading-overlay">
          <div class="spinner-border text-primary"></div>
        </div>

        <div v-else-if="doctors.length === 0" class="text-muted">No doctors in this department.</div>

        <div v-else class="row g-3">
          <div v-for="doc in doctors" :key="doc.doctor_id" class="col-md-6 col-lg-4">
            <div class="doc-card h-100">
              <div class="doc-card-accent"></div>
              <div class="doc-card-body">
                <div class="doc-card-header">
                  <div class="doc-avatar">{{ doc.name ? doc.name.charAt(0).toUpperCase() : '?' }}</div>
                  <div>
                    <h6>Dr. {{ doc.name }}</h6>
                    <p class="doc-spec">{{ doc.specialization }}</p>
                  </div>
                </div>

                <div v-if="doc.availability && Object.keys(doc.availability).length">
                  <div class="avail-section-label">Next 7 Days</div>
                  <table class="avail-table">
                    <tr v-for="d in getNext7Days()" :key="d.dateStr">
                      <td class="avail-day-label">{{ d.label }}</td>
                      <td>
                        <div v-if="doc.availability[d.day] && doc.availability[d.day].length > 0" class="avail-slots">
                          <span v-for="t in doc.availability[d.day]" :key="t" class="avail-slot">{{ t }}</span>
                        </div>
                        <span v-else class="on-leave-badge">On Leave</span>
                      </td>
                    </tr>
                  </table>
                </div>
                <div v-else class="text-muted mb-2" style="font-size:0.82rem">No availability set</div>

                <button class="btn-book" @click="openBook(doc)">
                  Book Appointment
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Book Modal -->
    <div v-if="showBookModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showBookModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Book with Dr. {{ bookForm.doctor_name }}</h5>
            <button class="btn-close" @click="showBookModal = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="bookError" class="alert alert-danger py-2" style="font-size:0.85rem">{{ bookError }}</div>

            <div class="mb-3">
              <label class="form-label">Date</label>
              <input v-model="bookForm.date" type="date" class="form-control" :min="todayStr" />
            </div>

            <div class="mb-3">
              <label class="form-label">Time</label>
              <div v-if="bookForm.date && allSlotsForDay().length > 0" class="d-flex flex-wrap gap-2 mb-2">
                <button
                  v-for="slot in allSlotsForDay()"
                  :key="slot"
                  class="slot-chip"
                  :class="{ active: bookForm.time === slot, booked: isSlotBooked(bookForm.date, slot) }"
                  :disabled="isSlotBooked(bookForm.date, slot)"
                  @click="!isSlotBooked(bookForm.date, slot) && (bookForm.time = slot)"
                  :style="isSlotBooked(bookForm.date, slot) ? 'cursor:not-allowed;opacity:0.5' : 'cursor:pointer'"
                >{{ slot }}<span v-if="isSlotBooked(bookForm.date, slot)" style="font-size:0.6rem;margin-left:2px">(Booked)</span></button>
              </div>
              <div v-else-if="bookForm.date && allSlotsForDay().length === 0" class="alert alert-warning py-2 mb-0" style="font-size:0.82rem">
                Doctor is on leave this day. Please pick another date.
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showBookModal = false">Cancel</button>
            <button class="btn btn-primary" @click="bookAppointment" :disabled="!bookForm.date || !bookForm.time || allSlotsForDay().length === 0">Book Now</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
