<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loggedIn = ref(false);
const role = ref(null);

onMounted(() => {
  const token = localStorage.getItem("token");
  role.value = localStorage.getItem("role");
  loggedIn.value = !!token;
});

const goToDashboard = () => {
  if (role.value) router.push("/" + role.value);
  else router.push("/login");
};
</script>

<template>
  <div style="background:var(--bg)">
    <!-- Navbar -->
    <nav class="landing-nav">
      <span class="landing-brand">HMS</span>
      <div class="d-flex gap-2">
        <template v-if="loggedIn">
          <button class="btn btn-primary btn-sm" @click="goToDashboard">Go to Dashboard</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn btn-outline-primary btn-sm">Sign In</router-link>
          <router-link to="/register" class="btn btn-primary btn-sm">Register</router-link>
        </template>
      </div>
    </nav>

    <!-- Hero -->
    <section class="landing-hero">
      <div class="landing-hero-inner">
        <span class="landing-badge">Secure. Reliable. Efficient.</span>
        <h1 class="landing-title">Hospital Management System</h1>
        <p class="landing-subtitle">
          A comprehensive web application designed to streamline hospital operations — 
          from patient registration and doctor scheduling to appointment tracking 
          and treatment record management. Built for administrators, doctors, and patients.
        </p>
        <div class="d-flex gap-2 justify-content-center">
          <router-link v-if="!loggedIn" to="/login" class="btn btn-primary">Sign In</router-link>
          <router-link v-if="!loggedIn" to="/register" class="btn" style="background:#fff;border:1px solid var(--border);color:var(--text)">Register as Patient</router-link>
          <button v-if="loggedIn" class="btn btn-primary" @click="goToDashboard">Open Dashboard</button>
        </div>
      </div>
    </section>

    <!-- Role Portals -->
    <section class="landing-section">
      <h2 class="landing-section-title">Three Dedicated Portals</h2>
      <p class="landing-section-desc">Each user role gets a tailored dashboard with the tools they need.</p>

      <div class="row g-3">
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <div class="landing-card-icon" style="background:#dbeafe;color:#2563eb">A</div>
              <h6 class="fw-bold mb-2">Admin Panel</h6>
              <ul class="landing-list">
                <li>Add, edit, and remove doctors and patients</li>
                <li>Manage departments and specializations</li>
                <li>View all appointments with status filters</li>
                <li>Dashboard with live stats and Chart.js visualizations</li>
              </ul>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <div class="landing-card-icon" style="background:#d1fae5;color:#16a34a">D</div>
              <h6 class="fw-bold mb-2">Doctor Portal</h6>
              <ul class="landing-list">
                <li>View today's and weekly appointment schedule</li>
                <li>Mark appointments as completed or cancelled</li>
                <li>Add treatment records — diagnosis, prescription, notes</li>
                <li>Set available time slots with an interactive weekly grid</li>
              </ul>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card h-100">
            <div class="card-body">
              <div class="landing-card-icon" style="background:#fef3c7;color:#d97706">P</div>
              <h6 class="fw-bold mb-2">Patient Portal</h6>
              <ul class="landing-list">
                <li>Browse departments and available doctors</li>
                <li>Book appointments based on doctor availability</li>
                <li>Cancel or reschedule upcoming appointments</li>
                <li>View visit history with full treatment details</li>
                <li>Export treatment records as CSV via background tasks</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Key Features -->
    <section class="landing-section" style="background:#fff;border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
      <h2 class="landing-section-title">Key Features</h2>
      <p class="landing-section-desc">Core capabilities that power the system.</p>
      <div class="row g-4">
        <div class="col-md-6">
          <div class="feature-card" style="border-left:3px solid #7c3aed">
            <div class="feature-card-header">
              <div class="landing-feature-icon" style="background:#ede9fe;color:#7c3aed">JWT</div>
              <h6 class="fw-bold mb-0">Authentication and Authorization</h6>
            </div>
            <p class="text-muted mb-0" style="font-size:0.84rem">Secure JWT-based login system with role-based access control. Each user role — admin, doctor, and patient — gets restricted access to only their permitted endpoints and views.</p>
          </div>
        </div>
        <div class="col-md-6">
          <div class="feature-card" style="border-left:3px solid #2563eb">
            <div class="feature-card-header">
              <div class="landing-feature-icon" style="background:#dbeafe;color:#2563eb">CRUD</div>
              <h6 class="fw-bold mb-0">Full CRUD Operations</h6>
            </div>
            <p class="text-muted mb-0" style="font-size:0.84rem">Complete create, read, update, and delete workflows for all entities — doctors, patients, departments, appointments, and treatment records — with search and filtering.</p>
          </div>
        </div>
        <div class="col-md-6">
          <div class="feature-card" style="border-left:3px solid #db2777">
            <div class="feature-card-header">
              <div class="landing-feature-icon" style="background:#fce7f3;color:#db2777">API</div>
              <h6 class="fw-bold mb-0">RESTful API Backend</h6>
            </div>
            <p class="text-muted mb-0" style="font-size:0.84rem">Flask-powered REST API with structured JSON responses, proper HTTP status codes, input validation, and server-side caching using Redis for performance optimization.</p>
          </div>
        </div>
        <div class="col-md-6">
          <div class="feature-card" style="border-left:3px solid #16a34a">
            <div class="feature-card-header">
              <div class="landing-feature-icon" style="background:#d1fae5;color:#16a34a">CSV</div>
              <h6 class="fw-bold mb-0">Background Task Processing</h6>
            </div>
            <p class="text-muted mb-0" style="font-size:0.84rem">Celery + Redis powered asynchronous task queue for heavy operations like exporting patient treatment history to CSV files without blocking the main application.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      Hospital Management System — 23F2004203
    </footer>
  </div>
</template>

<style scoped>
.landing-nav {
  background: #fff;
  border-bottom: 1px solid var(--border);
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 50;
}
.landing-brand {
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--text);
}

.landing-hero {
  background: linear-gradient(135deg, #eff6ff 0%, #f0fdf4 50%, #f5f3ff 100%);
  border-bottom: 1px solid var(--border);
  padding: 4.5rem 2rem 4rem;
  text-align: center;
}
.landing-hero-inner {
  max-width: 680px;
  margin: 0 auto;
}
.landing-badge {
  display: inline-block;
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 0.3rem 1rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 1.25rem;
}
.landing-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--text);
  line-height: 1.2;
  margin-bottom: 0.75rem;
}
.landing-subtitle {
  font-size: 1rem;
  color: var(--text-muted);
  line-height: 1.7;
  margin-bottom: 2rem;
}

.landing-section {
  padding: 3rem 2rem;
  max-width: 960px;
  margin: 0 auto;
}
.landing-section-title {
  font-size: 1.35rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 0.5rem;
  color: var(--text);
}
.landing-section-desc {
  text-align: center;
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.landing-card-icon {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.landing-list {
  padding-left: 1.1rem;
  margin: 0;
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.8;
}

.landing-feature-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 0.7rem;
  flex-shrink: 0;
}

.feature-card {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.25rem;
  height: 100%;
  box-shadow:
    0 1px 2px rgba(0,0,0,0.04),
    0 4px 12px rgba(0,0,0,0.06),
    0 8px 24px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.feature-card:hover {
  box-shadow:
    0 2px 4px rgba(0,0,0,0.05),
    0 8px 20px rgba(0,0,0,0.08),
    0 14px 36px rgba(0,0,0,0.06);
  transform: translateY(-2px);
}

.feature-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.landing-footer {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.8rem;
  border-top: 1px solid var(--border);
}
</style>

