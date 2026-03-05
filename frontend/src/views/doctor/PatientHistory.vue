<script setup>
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import api from "../../api/axios";

const route = useRoute();
const patientId = route.params.id;
const patientInfo = ref(null);
const history = ref([]);
const loading = ref(true);

// Edit treatment modal
const showEditModal = ref(false);
const editTreatment = ref({ id: null, diagnosis: "", prescription: "", notes: "", next_visit: "" });

const fetchHistory = async () => {
  loading.value = true;
  try {
    const res = await api.get("/doctor/patient/" + patientId + "/history");
    patientInfo.value = res.data.patient;
    history.value = res.data.history;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const openEditTreatment = (h) => {
  editTreatment.value = {
    id: h.treatment.id,
    diagnosis: h.treatment.diagnosis || "",
    prescription: h.treatment.prescription || "",
    notes: h.treatment.notes || "",
    next_visit: h.treatment.next_visit || "",
  };
  showEditModal.value = true;
};

const saveTreatment = async () => {
  try {
    await api.put("/doctor/treatments/" + editTreatment.value.id, {
      diagnosis: editTreatment.value.diagnosis,
      prescription: editTreatment.value.prescription,
      notes: editTreatment.value.notes,
      next_visit: editTreatment.value.next_visit,
    });
    showEditModal.value = false;
    fetchHistory();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to update treatment");
  }
};

onMounted(fetchHistory);
</script>

<template>
  <div>
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else>
      <div v-if="patientInfo" class="card mb-4">
        <div class="card-body">
          <h5 class="fw-bold mb-1">{{ patientInfo.name }}</h5>
          <div class="text-muted" style="font-size:0.85rem">
            {{ patientInfo.age }} years | {{ patientInfo.gender }} | Phone: {{ patientInfo.phone || 'N/A' }}
          </div>
          <div class="text-muted" style="font-size:0.82rem">Address: {{ patientInfo.address || 'N/A' }}</div>
        </div>
      </div>

      <h6 class="fw-bold mb-3">Visit History ({{ history.length }})</h6>

      <div v-if="history.length === 0" class="empty-state">
        <p>No visit records found.</p>
      </div>

      <div v-for="h in history" :key="h.appointment_id" class="card mb-3">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-center mb-2">
            <div>
              <strong>{{ h.date }}</strong> at {{ h.time }}
              <span :class="h.status === 'Completed' ? 'badge-status badge-completed ms-2' : h.status === 'Cancelled' ? 'badge-status badge-cancelled ms-2' : 'badge-status badge-booked ms-2'">
                {{ h.status }}
              </span>
            </div>
            <button
              v-if="h.treatment"
              class="btn btn-sm btn-outline-primary"
              @click="openEditTreatment(h)"
            >
              Edit Treatment
            </button>
          </div>

          <div v-if="h.treatment" class="bg-light p-3 rounded mt-2" style="font-size:0.85rem">
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
          <div v-else class="text-muted mt-2" style="font-size:0.85rem">
            No treatment record for this visit.
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Treatment Modal -->
    <div v-if="showEditModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showEditModal = false">
      <div class="modal-dialog modal-dialog-centered modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Treatment Record</h5>
            <button class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Diagnosis *</label>
              <textarea v-model="editTreatment.diagnosis" class="form-control" rows="2"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Prescription *</label>
              <textarea v-model="editTreatment.prescription" class="form-control" rows="2"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Notes</label>
              <textarea v-model="editTreatment.notes" class="form-control" rows="2"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">Next Visit Date</label>
              <input v-model="editTreatment.next_visit" type="date" class="form-control" />
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
            <button class="btn btn-primary" @click="saveTreatment">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
