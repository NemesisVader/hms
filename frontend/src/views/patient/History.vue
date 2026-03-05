<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const history = ref([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const res = await api.get("/patient/appointments/history");
    history.value = res.data;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
});
</script>

<template>
  <div>
    <div class="section-header">
      <h4>Visit History ({{ history.length }})</h4>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="history.length === 0" class="empty-state">
      <p>No past appointments found.</p>
    </div>

    <div v-else>
      <div v-for="h in history" :key="h.appointment_id" class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
              <strong>{{ h.date }}</strong> at {{ h.time }}
              <span class="text-muted ms-2">- Dr. {{ h.doctor }}</span>
            </div>
            <span :class="h.status === 'Completed' ? 'badge-status badge-completed' : h.status === 'Cancelled' ? 'badge-status badge-cancelled' : 'badge-status badge-booked'">
              {{ h.status }}
            </span>
          </div>

          <div v-if="h.treatment" class="bg-light p-3 rounded" style="font-size:0.85rem">
            <div class="row g-2">
              <div class="col-md-6">
                <strong>Diagnosis:</strong>
                <p class="mb-1">{{ h.treatment.diagnosis }}</p>
              </div>
              <div class="col-md-6">
                <strong>Prescription:</strong>
                <p class="mb-1">{{ h.treatment.prescription }}</p>
              </div>
              <div class="col-md-6">
                <strong>Notes:</strong>
                <p class="mb-1">{{ h.treatment.notes || 'None' }}</p>
              </div>
              <div class="col-md-6">
                <strong>Next Visit:</strong>
                <p class="mb-1">{{ h.treatment.next_visit || 'Not scheduled' }}</p>
              </div>
            </div>
          </div>
          <div v-else class="text-muted mt-1" style="font-size:0.85rem">
            No treatment details recorded.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
