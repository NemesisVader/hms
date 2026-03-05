<script setup>
import { ref } from "vue";
import api from "../../api/axios";

const exporting = ref(false);
const message = ref("");
const taskId = ref(null);
const exportDone = ref(false);
const downloading = ref(false);

let pollInterval = null;

const triggerExport = async () => {
  exporting.value = true;
  message.value = "";
  taskId.value = null;
  exportDone.value = false;
  try {
    const res = await api.post("/patient/export_treatments");
    taskId.value = res.data.task_id;
    message.value = "Export started! Checking progress...";
    startPolling();
  } catch (e) {
    message.value = e.response?.data?.msg || "Export failed";
    exporting.value = false;
  }
};

const startPolling = () => {
  clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const res = await api.get("/patient/export_treatments/status/" + taskId.value);
      if (res.data.status === "done") {
        clearInterval(pollInterval);
        exporting.value = false;
        exportDone.value = true;
        message.value = "Export complete! Click below to download your CSV.";
      } else if (res.data.status === "failed") {
        clearInterval(pollInterval);
        exporting.value = false;
        message.value = "Export failed: " + (res.data.msg || "Unknown error");
      }
    } catch (e) {
    }
  }, 2000);
};

const downloadCsv = async () => {
  downloading.value = true;
  try {
    const res = await api.get("/patient/export_treatments/download", {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "treatment_history.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    message.value = "Download failed. Please try exporting again.";
  } finally {
    downloading.value = false;
  }
};
</script>

<template>
  <div style="max-width:550px">
    <div class="section-header">
      <h4>Export Treatment Data</h4>
    </div>

    <div class="card">
      <div class="card-body text-center py-4">
        <h6 class="fw-bold mb-2">Export Treatment History</h6>
        <p class="text-muted mb-3" style="font-size:0.85rem">
          Download a CSV file containing your complete treatment records including
          doctor names, appointment dates, diagnosis, prescriptions, and notes.
        </p>

        <button
          class="btn btn-primary"
          @click="triggerExport"
          :disabled="exporting"
        >
          <span v-if="exporting">
            <span class="spinner-border spinner-border-sm me-1"></span> Exporting...
          </span>
          <span v-else>Export as CSV</span>
        </button>

        <div v-if="message" class="alert mt-3" :class="exportDone ? 'alert-success' : taskId && !exportDone ? 'alert-info' : 'alert-danger'" style="font-size:0.85rem">
          {{ message }}
          <div v-if="taskId && !exportDone" class="mt-1 text-muted" style="font-size:0.78rem">
            Task ID: {{ taskId }}
          </div>
        </div>

        <div v-if="exportDone" class="mt-3">
          <button
            class="btn btn-success"
            @click="downloadCsv"
            :disabled="downloading"
          >
            <span v-if="downloading">
              <span class="spinner-border spinner-border-sm me-1"></span> Downloading...
            </span>
            <span v-else>Download CSV</span>
          </button>
        </div>
      </div>
    </div>

    <div class="card mt-3">
      <div class="card-body" style="font-size:0.82rem">
        <h6 class="fw-bold mb-2" style="font-size:0.9rem">CSV Fields</h6>
        <div class="row g-1">
          <div class="col-6"><span class="text-muted">•</span> User ID</div>
          <div class="col-6"><span class="text-muted">•</span> Username</div>
          <div class="col-6"><span class="text-muted">•</span> Consulting Doctor</div>
          <div class="col-6"><span class="text-muted">•</span> Appointment Date</div>
          <div class="col-6"><span class="text-muted">•</span> Appointment Time</div>
          <div class="col-6"><span class="text-muted">•</span> Status</div>
          <div class="col-6"><span class="text-muted">•</span> Diagnosis</div>
          <div class="col-6"><span class="text-muted">•</span> Treatment/Prescription</div>
          <div class="col-6"><span class="text-muted">•</span> Doctor Notes</div>
          <div class="col-6"><span class="text-muted">•</span> Next Visit</div>
        </div>
      </div>
    </div>
  </div>
</template>
