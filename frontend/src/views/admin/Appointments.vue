<script setup>
import { ref, computed, onMounted } from "vue";
import api from "../../api/axios";

const appointments = ref([]);
const loading = ref(true);
const total = ref(0);
const statusFilter = ref("");
const dateFilter = ref("");
const searchQuery = ref("");
const activeTab = ref("all"); // all | upcoming | past

const fetchAppointments = async () => {
  loading.value = true;
  try {
    const params = { page: 1, per_page: 500 };
    if (statusFilter.value) params.status = statusFilter.value;
    if (dateFilter.value) params.date = dateFilter.value;
    const res = await api.get("/admin/appointments", { params });
    appointments.value = res.data.items || [];
    total.value = res.data.total;
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const todayStr = new Date().toISOString().slice(0, 10);

const filteredAppointments = computed(() => {
  let list = appointments.value;

  // Tab filter: upcoming vs past
  if (activeTab.value === "upcoming") {
    list = list.filter(a => a.date >= todayStr);
  } else if (activeTab.value === "past") {
    list = list.filter(a => a.date < todayStr);
  }

  // Search filter (patient or doctor name)
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase();
    list = list.filter(a =>
      (a.patient && a.patient.toLowerCase().includes(q)) ||
      (a.doctor && a.doctor.toLowerCase().includes(q))
    );
  }

  return list;
});

const badgeClass = (status) => {
  if (status === "Booked") return "badge-status badge-booked";
  if (status === "Completed") return "badge-status badge-completed";
  if (status === "Cancelled") return "badge-status badge-cancelled";
  return "badge bg-secondary";
};

const setTab = (tab) => {
  activeTab.value = tab;
};

const clearFilters = () => {
  statusFilter.value = "";
  dateFilter.value = "";
  searchQuery.value = "";
  activeTab.value = "all";
  fetchAppointments();
};

// Status update
const updateStatus = async (apptId, newStatus) => {
  try {
    await api.put(`/admin/appointments/${apptId}/status`, { status: newStatus });
    // Update locally for instant feedback
    const appt = appointments.value.find(a => a.appointment_id === apptId);
    if (appt) appt.status = newStatus;
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to update status");
  }
};

onMounted(fetchAppointments);
</script>

<template>
  <div>
    <!-- Header -->
    <div class="section-header">
      <h4>Appointments ({{ filteredAppointments.length }}<span v-if="filteredAppointments.length !== total" class="text-muted" style="font-size:0.75rem"> / {{ total }} total</span>)</h4>
    </div>

    <!-- Tabs -->
    <div class="d-flex gap-2 mb-3 flex-wrap align-items-center">
      <div class="btn-group" role="group">
        <button
          class="btn btn-sm"
          :class="activeTab === 'all' ? 'btn-primary' : 'btn-outline-primary'"
          @click="setTab('all')"
        >
          All
        </button>
        <button
          class="btn btn-sm"
          :class="activeTab === 'upcoming' ? 'btn-success' : 'btn-outline-success'"
          @click="setTab('upcoming')"
        >
          Upcoming
        </button>
        <button
          class="btn btn-sm"
          :class="activeTab === 'past' ? 'btn-secondary' : 'btn-outline-secondary'"
          @click="setTab('past')"
        >
          Past
        </button>
      </div>

      <select v-model="statusFilter" class="form-select form-select-sm" style="width:140px" @change="fetchAppointments">
        <option value="">All Statuses</option>
        <option value="Booked">Booked</option>
        <option value="Completed">Completed</option>
        <option value="Cancelled">Cancelled</option>
      </select>

      <input
        type="date"
        v-model="dateFilter"
        class="form-control form-control-sm"
        style="width:160px"
        @change="fetchAppointments"
      />

      <input
        v-model="searchQuery"
        class="form-control form-control-sm"
        placeholder="Search patient or doctor..."
        style="width:200px"
      />

      <button v-if="statusFilter || dateFilter || searchQuery || activeTab !== 'all'" class="btn btn-sm btn-outline-danger" @click="clearFilters">
        Clear
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <!-- Empty State -->
    <div v-else-if="filteredAppointments.length === 0" class="empty-state">
      <p>No appointments found.</p>
    </div>

    <!-- Table -->
    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Patient</th>
              <th>Doctor</th>
              <th>Date</th>
              <th>Time</th>
              <th>Status</th>
              <th style="width:180px">Update Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in filteredAppointments" :key="a.appointment_id">
              <td>{{ a.appointment_id }}</td>
              <td class="fw-semibold">{{ a.patient }}</td>
              <td>{{ a.doctor }}</td>
              <td>
                <span :class="a.date >= todayStr ? 'text-success' : 'text-muted'">{{ a.date }}</span>
              </td>
              <td>{{ a.time }}</td>
              <td><span :class="badgeClass(a.status)">{{ a.status }}</span></td>
              <td>
                <div class="d-flex gap-1">
                  <!-- Booked → can Complete or Cancel -->
                  <template v-if="a.status === 'Booked'">
                    <button class="btn btn-sm btn-outline-success" @click="updateStatus(a.appointment_id, 'Completed')">✓ Complete</button>
                    <button class="btn btn-sm btn-outline-danger" @click="updateStatus(a.appointment_id, 'Cancelled')">✕ Cancel</button>
                  </template>
                  <!-- Completed or Cancelled → can only Rebook -->
                  <template v-else>
                    <button class="btn btn-sm btn-outline-primary" @click="updateStatus(a.appointment_id, 'Booked')">↺ Rebook</button>
                  </template>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>