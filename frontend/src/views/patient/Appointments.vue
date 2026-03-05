<script setup>
import { ref, onMounted, computed } from "vue";
import api from "../../api/axios";

const appointments = ref([]);
const todayStr = new Date().toISOString().split('T')[0];
const loading = ref(true);
const showReschedule = ref(false);
const rescheduleAppt = ref(null);
const rescheduleForm = ref({ date: "", time: "" });
const rescheduleError = ref("");
const doctorAvailability = ref({});
const doctorBookedSlots = ref({});

const badgeClass = (status) => {
  if (status === "Booked") return "badge-status badge-booked";
  if (status === "Completed") return "badge-status badge-completed";
  if (status === "Cancelled") return "badge-status badge-cancelled";
  return "badge bg-secondary";
};

const fetchAppointments = async () => {
  loading.value = true;
  try {
    const res = await api.get("/patient/appointments/upcoming");
    appointments.value = res.data;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const cancelAppointment = async (id) => {
  if (!confirm("Cancel this appointment?")) return;
  try {
    await api.put("/patient/appointments/" + id + "/cancel");
    fetchAppointments();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to cancel");
  }
};

const openReschedule = async (appt) => {
  rescheduleAppt.value = appt;
  rescheduleForm.value = { date: "", time: "" };
  rescheduleError.value = "";
  doctorAvailability.value = {};
  doctorBookedSlots.value = {};
  try {
    const res = await api.get("/patient/doctors/" + appt.doctor_id + "/availability");
    doctorAvailability.value = res.data.availability || {};
    doctorBookedSlots.value = res.data.booked_slots || {};
  } catch { doctorAvailability.value = {}; doctorBookedSlots.value = {}; }
  showReschedule.value = true;
};

const allSlotsForDay = computed(() => {
  if (!rescheduleForm.value.date || !doctorAvailability.value) return [];
  try {
    const dt = new Date(rescheduleForm.value.date);
    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const dayName = dayNames[dt.getDay()];
    return doctorAvailability.value[dayName] || [];
  } catch { return []; }
});

const isSlotBooked = (time) => {
  if (!rescheduleForm.value.date) return false;
  const booked = doctorBookedSlots.value[rescheduleForm.value.date] || [];
  return booked.includes(time);
};

const availableSlots = computed(() => {
  return allSlotsForDay.value.filter(t => !isSlotBooked(t));
});

const reschedule = async () => {
  rescheduleError.value = "";
  if (!rescheduleForm.value.date || !rescheduleForm.value.time) {
    rescheduleError.value = "Date and time required";
    return;
  }
  try {
    await api.put("/patient/appointments/" + rescheduleAppt.value.appointment_id + "/reschedule", {
      date: rescheduleForm.value.date,
      time: rescheduleForm.value.time,
    });
    showReschedule.value = false;
    fetchAppointments();
  } catch (e) {
    rescheduleError.value = e.response?.data?.msg || "Reschedule failed";
  }
};

onMounted(fetchAppointments);
</script>

<template>
  <div>
    <div class="section-header">
      <h4>My Appointments ({{ appointments.length }})</h4>
      <router-link to="/patient" class="btn btn-primary btn-sm">+ Book New</router-link>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="appointments.length === 0" class="empty-state">
      <p>No upcoming appointments.</p>
      <router-link to="/patient" class="btn btn-primary btn-sm">Browse Doctors & Book</router-link>
    </div>

    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Doctor</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in appointments" :key="a.appointment_id">
              <td>{{ a.appointment_id }}</td>
              <td class="fw-semibold">Dr. {{ a.doctor_name }}</td>
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td><span :class="badgeClass(a.status)">{{ a.status }}</span></td>
              <td>
                <div v-if="a.status === 'Booked'" class="d-flex gap-1">
                  <button class="btn btn-sm btn-outline-primary" @click="openReschedule(a)">Reschedule</button>
                  <button class="btn btn-sm btn-outline-danger" @click.stop="cancelAppointment(a.appointment_id)">Cancel</button>
                </div>
                <span v-else class="text-muted">-</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Reschedule Modal -->
    <div v-if="showReschedule" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showReschedule = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Reschedule Appointment</h5>
            <button class="btn-close" @click="showReschedule = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="rescheduleError" class="alert alert-danger py-2" style="font-size:0.85rem">{{ rescheduleError }}</div>
            <div class="mb-3">
              <label class="form-label">New Date</label>
              <input v-model="rescheduleForm.date" type="date" class="form-control" :min="todayStr" />
            </div>
            <div class="mb-3">
              <label class="form-label">New Time</label>
              <div v-if="rescheduleForm.date && allSlotsForDay.length > 0" class="d-flex flex-wrap gap-2 mb-2">
                <button
                  v-for="slot in allSlotsForDay"
                  :key="slot"
                  class="slot-chip"
                  :class="{ active: rescheduleForm.time === slot, booked: isSlotBooked(slot) }"
                  :disabled="isSlotBooked(slot)"
                  @click="!isSlotBooked(slot) && (rescheduleForm.time = slot)"
                  :style="isSlotBooked(slot) ? 'cursor:not-allowed;opacity:0.5' : 'cursor:pointer'"
                >{{ slot }}<span v-if="isSlotBooked(slot)" style="font-size:0.6rem;margin-left:2px">(Booked)</span></button>
              </div>
              <div v-else-if="rescheduleForm.date && allSlotsForDay.length === 0" class="alert alert-warning py-2 mb-0" style="font-size:0.82rem">
                Doctor is on leave this day. Please pick another date.
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showReschedule = false">Cancel</button>
            <button class="btn btn-primary" @click="reschedule" :disabled="!rescheduleForm.date || !rescheduleForm.time || allSlotsForDay.length === 0">Reschedule</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
