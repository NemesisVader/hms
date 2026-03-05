<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";
import { Bar, Doughnut } from "vue-chartjs";
import {
  Chart as ChartJS,
  Title, Tooltip, Legend,
  BarElement, CategoryScale, LinearScale,
  ArcElement,
} from "chart.js";

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement);

const stats = ref(null);
const loading = ref(true);
const appointments = ref([]);

onMounted(async () => {
  try {
    const [statsRes, apptRes] = await Promise.all([
      api.get("/admin/dashboard"),
      api.get("/admin/appointments", { params: { per_page: 200 } }),
    ]);
    stats.value = statsRes.data;
    appointments.value = apptRes.data.items || [];
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
});

const barChartData = () => {
  return {
    labels: ["Doctors", "Patients", "Departments", "Appointments"],
    datasets: [{
      label: "Count",
      data: [
        stats.value.doctors,
        stats.value.patients,
        stats.value.departments,
        stats.value.appointments,
      ],
      backgroundColor: ["#0d6efd", "#198754", "#6f42c1", "#fd7e14"],
      borderRadius: 4,
    }],
  };
};

const barChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: { display: true, text: "System Overview", font: { size: 14, weight: "600" } },
  },
  scales: {
    y: { beginAtZero: true, ticks: { stepSize: 1 } },
  },
};

const doughnutChartData = () => {
  const booked = appointments.value.filter(a => a.status === "Booked").length;
  const completed = appointments.value.filter(a => a.status === "Completed").length;
  const cancelled = appointments.value.filter(a => a.status === "Cancelled").length;

  return {
    labels: ["Booked", "Completed", "Cancelled"],
    datasets: [{
      data: [booked, completed, cancelled],
      backgroundColor: ["#0d6efd", "#198754", "#dc3545"],
      borderWidth: 0,
    }],
  };
};

const doughnutChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    title: { display: true, text: "Appointment Status", font: { size: 14, weight: "600" } },
    legend: { position: "bottom", labels: { padding: 15, font: { size: 12 } } },
  },
};
</script>

<template>
  <div>
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="stats">
      <!-- Stat Cards -->
      <div class="row g-3 mb-4">
        <div class="col-md-4 col-sm-6">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number text-primary">{{ stats.doctors }}</div>
                <div class="stat-label">Doctors</div>
              </div>
              <div class="stat-icon" style="background:#e7f1ff;color:#0d6efd">D</div>
            </div>
          </div>
        </div>

        <div class="col-md-4 col-sm-6">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number text-success">{{ stats.patients }}</div>
                <div class="stat-label">Patients</div>
              </div>
              <div class="stat-icon" style="background:#d1e7dd;color:#146c43">P</div>
            </div>
          </div>
        </div>

        <div class="col-md-4 col-sm-6">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number" style="color:#fd7e14">{{ stats.appointments }}</div>
                <div class="stat-label">Total Appointments</div>
              </div>
              <div class="stat-icon" style="background:#fff3cd;color:#997404">A</div>
            </div>
          </div>
        </div>

        <div class="col-md-4 col-sm-6">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number" style="color:#6f42c1">{{ stats.departments }}</div>
                <div class="stat-label">Departments</div>
              </div>
              <div class="stat-icon" style="background:#e8dff5;color:#6f42c1">Dp</div>
            </div>
          </div>
        </div>

        <div class="col-md-4 col-sm-6">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number text-info">{{ stats.today_appointments }}</div>
                <div class="stat-label">Today</div>
              </div>
              <div class="stat-icon" style="background:#cff4fc;color:#087990">T</div>
            </div>
          </div>
        </div>

        <div class="col-md-4 col-sm-6">
          <div class="card stat-card">
            <div class="card-body d-flex align-items-center justify-content-between">
              <div>
                <div class="stat-number text-danger">{{ stats.upcoming_7days_appointments }}</div>
                <div class="stat-label">Upcoming 7 days</div>
              </div>
              <div class="stat-icon" style="background:#f8d7da;color:#842029">U</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Charts -->
      <div class="row g-3">
        <div class="col-md-7">
          <div class="card">
            <div class="card-body" style="height: 320px">
              <Bar :data="barChartData()" :options="barChartOptions" />
            </div>
          </div>
        </div>
        <div class="col-md-5">
          <div class="card">
            <div class="card-body" style="height: 320px">
              <Doughnut v-if="appointments.length > 0" :data="doughnutChartData()" :options="doughnutChartOptions" />
              <div v-else class="d-flex align-items-center justify-content-center h-100 text-muted">
                No appointment data for chart
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Appointments -->
      <div class="row g-3 mt-1">
        <div class="col-12">
          <div class="card">
            <div class="card-body">
              <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 fw-bold">Recent Appointments</h6>
                <router-link to="/admin/appointments" class="btn btn-sm btn-outline-primary">View All</router-link>
              </div>
              <div v-if="appointments.length === 0" class="text-muted text-center py-3">
                No appointments yet.
              </div>
              <table v-else class="table table-hover mb-0">
                <thead>
                  <tr>
                    <th>Patient</th>
                    <th>Doctor</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="a in appointments.slice(0, 5)" :key="a.appointment_id">
                    <td class="fw-semibold">{{ a.patient }}</td>
                    <td>{{ a.doctor }}</td>
                    <td>{{ a.date }}</td>
                    <td>{{ a.time }}</td>
                    <td>
                      <span class="badge" :style="a.status === 'Booked' ? 'background:#dbeafe;color:#1d4ed8' : a.status === 'Completed' ? 'background:#d1fae5;color:#16a34a' : 'background:#fee2e2;color:#dc2626'">
                        {{ a.status }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>