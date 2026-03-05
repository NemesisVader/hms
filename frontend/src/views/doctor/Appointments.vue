<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";
import { useRouter } from "vue-router";

const router = useRouter();

const appointments = ref([]);
const loading = ref(true);
const showTreatmentModal = ref(false);
const treatmentApptId = ref(null);
const treatmentForm = ref({ diagnosis: "", prescription: "", notes: "", next_visit: "" });

const badgeClass = (status) => {
  if (status === "Booked") return "badge-status badge-booked";
  if (status === "Completed") return "badge-status badge-completed";
  if (status === "Cancelled") return "badge-status badge-cancelled";
  return "badge bg-secondary";
};

const fetchAppointments = async () => {
  loading.value = true;
  try {
    const res = await api.get("/doctor/appointments");
    appointments.value = res.data;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const updateStatus = async (apptId, status) => {
  if (!confirm("Mark this appointment as " + status + "?")) return;
  try {
    await api.put("/doctor/appointments/" + apptId + "/status", { status });
    fetchAppointments();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed");
  }
};

const openTreatment = (apptId) => {
  treatmentApptId.value = apptId;
  treatmentForm.value = { diagnosis: "", prescription: "", notes: "", next_visit: "" };
  showTreatmentModal.value = true;
};

const addTreatment = async () => {
  try {
    await api.post("/doctor/appointments/" + treatmentApptId.value + "/treatment", treatmentForm.value);
    showTreatmentModal.value = false;
    fetchAppointments();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to add treatment");
  }
};

onMounted(fetchAppointments);
</script>

<template>
  <div>
    <div class="section-header">
      <h4>My Appointments ({{ appointments.length }})</h4>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="appointments.length === 0" class="empty-state">
      <p>No appointments found.</p>
    </div>

    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Patient</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in appointments" :key="a.appointment_id">
              <td>{{ a.appointment_id }}</td>
              <td class="fw-semibold">
                <a href="#" class="text-decoration-none" @click.prevent="router.push('/doctor/patient/' + a.patient_id)" v-if="a.patient_id">
                  {{ a.patient }}
                </a>
                <span v-else>{{ a.patient }}</span>
              </td>
              <td>{{ a.date }}</td>
              <td>{{ a.time }}</td>
              <td><span :class="badgeClass(a.status)">{{ a.status }}</span></td>
              <td>
                <div class="d-flex gap-1 flex-wrap">
                  <button
                    v-if="a.status === 'Booked'"
                    class="btn btn-sm btn-success"
                    @click="updateStatus(a.appointment_id, 'Completed')"
                  >Complete</button>
                  <button
                    v-if="a.status === 'Booked'"
                    class="btn btn-sm btn-outline-danger"
                    @click="updateStatus(a.appointment_id, 'Cancelled')"
                  >Cancel</button>
                  <button
                    class="btn btn-sm btn-outline-primary"
                    @click="openTreatment(a.appointment_id)"
                  >Add Treatment</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Treatment Modal -->
    <div v-if="showTreatmentModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showTreatmentModal = false">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add Treatment - Appointment #{{ treatmentApptId }}</h5>
            <button class="btn-close" @click="showTreatmentModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Diagnosis *</label>
              <textarea v-model="treatmentForm.diagnosis" class="form-control" rows="2" placeholder="Enter diagnosis"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Prescription *</label>
              <textarea v-model="treatmentForm.prescription" class="form-control" rows="2" placeholder="Enter prescription"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea v-model="treatmentForm.notes" class="form-control" rows="2" placeholder="Additional notes"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Next Visit Date</label>
              <input v-model="treatmentForm.next_visit" type="date" class="form-control" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showTreatmentModal = false">Cancel</button>
            <button class="btn btn-primary" @click="addTreatment">Save Treatment</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
