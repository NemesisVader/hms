<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";
import { useRouter } from "vue-router";

const router = useRouter();
const patients = ref([]);
const loading = ref(true);
const searchQuery = ref("");

const fetchPatients = async () => {
  loading.value = true;
  try {
    const res = await api.get("/doctor/patients");
    patients.value = res.data;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const filteredPatients = () => {
  if (!searchQuery.value.trim()) return patients.value;
  const q = searchQuery.value.toLowerCase();
  return patients.value.filter(p =>
    p.name.toLowerCase().includes(q) ||
    (p.phone && p.phone.includes(q))
  );
};

const goToHistory = (patientId) => {
  router.push("/doctor/patient/" + patientId);
};

onMounted(fetchPatients);
</script>

<template>
  <div>
    <div class="section-header">
      <h4>My Patients ({{ patients.length }})</h4>
      <div class="search-bar">
        <input
          v-model="searchQuery"
          class="form-control"
          placeholder="Search by name or phone..."
          style="min-width:220px"
        />
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="filteredPatients().length === 0" class="empty-state">
      <p>No patients found.</p>
    </div>

    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Age</th>
              <th>Gender</th>
              <th>Phone</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filteredPatients()" :key="p.patient_id">
              <td>{{ p.patient_id }}</td>
              <td class="fw-semibold">{{ p.name }}</td>
              <td>{{ p.age }}</td>
              <td>{{ p.gender }}</td>
              <td>{{ p.phone || '-' }}</td>
              <td>
                <button class="btn btn-sm btn-outline-primary" @click="goToHistory(p.patient_id)">
                  View History
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
