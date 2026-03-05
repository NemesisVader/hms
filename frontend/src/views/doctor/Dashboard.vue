<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";
import { useRouter } from "vue-router";

const router = useRouter();
const todayAppts = ref([]);
const weekAppts = ref([]);
const patients = ref([]);
const loading = ref(true);

const badgeClass = (status) => {
  if (status === "Booked") return "badge-status badge-booked";
  if (status === "Completed") return "badge-status badge-completed";
  if (status === "Cancelled") return "badge-status badge-cancelled";
  return "badge bg-secondary";
};

const updateStatus = async (apptId, status) => {
  try {
    await api.put("/doctor/appointments/" + apptId + "/status", { status });
    // Update locally
    const appt = todayAppts.value.find(a => a.appointment_id === apptId);
    if (appt) appt.status = status;
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to update status");
  }
};

const goToHistory = (patientId) => {
  router.push("/doctor/patient/" + patientId);
};

onMounted(async () => {
  try {
    const [todayRes, weekRes, patientsRes] = await Promise.all([
      api.get("/doctor/appointments/today"),
      api.get("/doctor/appointments/week"),
      api.get("/doctor/patients"),
    ]);
    todayAppts.value = todayRes.data;
    weekAppts.value = weekRes.data;
    patients.value = patientsRes.data;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
});
</script>

<template>
  <div>
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <!-- Stat Cards -->
      <div class="row g-3 mb-4">
        <div class="col-md-4">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number text-primary">{{ todayAppts.length }}</div>
                <div class="stat-label">Today's Appointments</div>
              </div>
              <div class="stat-icon" style="background:#e7f1ff;color:#0d6efd">T</div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number text-success">{{ weekAppts.length }}</div>
                <div class="stat-label">This Week</div>
              </div>
              <div class="stat-icon" style="background:#d1e7dd;color:#146c43">W</div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number" style="color:#6f42c1">{{ patients.length }}</div>
                <div class="stat-label">My Patients</div>
              </div>
              <div class="stat-icon" style="background:#e8dff5;color:#6f42c1">P</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Today's Appointments with Actions -->
      <div class="card mb-4">
        <div class="card-body">
          <h6 class="fw-bold mb-3">Today's Appointments</h6>
          <div v-if="todayAppts.length === 0" class="text-muted">No appointments today.</div>
          <table v-else class="table table-hover mb-0">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Time</th>
                <th>Status</th>
                <th style="width:180px">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="a in todayAppts" :key="a.appointment_id">
                <td class="fw-semibold">{{ a.patient }}</td>
                <td>{{ a.time }}</td>
                <td><span :class="badgeClass(a.status)">{{ a.status }}</span></td>
                <td>
                  <div class="d-flex gap-1">
                    <template v-if="a.status === 'Booked'">
                      <button class="btn btn-sm btn-success" @click="updateStatus(a.appointment_id, 'Completed')">✓ Complete</button>
                      <button class="btn btn-sm btn-outline-danger" @click="updateStatus(a.appointment_id, 'Cancelled')">✕ Cancel</button>
                    </template>
                    <span v-else class="text-muted" style="font-size:0.82rem">{{ a.status }}</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- My Patients -->
      <div class="card">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="fw-bold mb-0">My Patients</h6>
            <router-link to="/doctor/patients" class="btn btn-sm btn-outline-primary">View All</router-link>
          </div>
          <div v-if="patients.length === 0" class="text-muted">No patients assigned yet.</div>
          <table v-else class="table table-hover mb-0">
            <thead>
              <tr>
                <th>Name</th>
                <th>Age</th>
                <th>Gender</th>
                <th>Phone</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="p in patients.slice(0, 5)" :key="p.patient_id">
                <td class="fw-semibold">{{ p.name }}</td>
                <td>{{ p.age }}</td>
                <td>{{ p.gender }}</td>
                <td>{{ p.phone || '-' }}</td>
                <td>
                  <button class="btn btn-sm btn-outline-primary" @click="goToHistory(p.patient_id)">View History</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
