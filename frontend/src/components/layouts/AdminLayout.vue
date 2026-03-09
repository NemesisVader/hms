<template>
  <div class="d-flex" style="height: 100vh; overflow: hidden;">
    <div class="sidebar p-0" style="width: 220px;">
      <div class="sidebar-brand">HMS Admin</div>

      <div class="sidebar-nav">
        <router-link to="/admin">Dashboard</router-link>
        <router-link to="/admin/doctors">Doctors</router-link>
        <router-link to="/admin/patients">Patients</router-link>
        <router-link to="/admin/appointments">Appointments</router-link>
        <router-link to="/admin/departments">Departments</router-link>
      </div>

      <div class="sidebar-footer">
        <button class="btn btn-sm btn-outline-light w-100" @click="logout">
          Logout
        </button>
      </div>
    </div>

    <div class="flex-fill d-flex flex-column" style="min-width:0; overflow: hidden;">
      <div class="top-header">
        <h5>{{ pageTitle }}</h5>
        <span class="text-muted" style="font-size:0.82rem">{{ username }}</span>
      </div>

      <div class="content-area flex-fill" style="overflow-y: auto;">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";

const router = useRouter();
const route = useRoute();

const username = localStorage.getItem("username") || "Admin";

const pageTitle = computed(() => {
  const path = route.path;
  if (path === "/admin") return "Dashboard";
  if (path.includes("doctors")) return "Manage Doctors";
  if (path.includes("patients")) return "Manage Patients";
  if (path.includes("appointments")) return "All Appointments";
  if (path.includes("departments")) return "Departments";
  return "Admin Panel";
});

const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  router.push("/login");
};
</script>