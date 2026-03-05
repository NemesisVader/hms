<template>
  <div class="d-flex">
    <div class="sidebar p-0" style="width: 220px;">
      <div class="sidebar-brand">HMS Patient</div>

      <div class="sidebar-nav">
        <router-link to="/patient">Dashboard</router-link>
        <router-link to="/patient/appointments">My Appointments</router-link>
        <router-link to="/patient/history">History</router-link>
        <router-link to="/patient/profile">Profile</router-link>
        <router-link to="/patient/export">Export Data</router-link>
      </div>

      <div class="sidebar-footer">
        <button class="btn btn-sm btn-outline-light w-100" @click="logout">Logout</button>
      </div>
    </div>

    <div class="flex-fill" style="min-width:0">
      <div class="top-header">
        <h5>{{ pageTitle }}</h5>
        <span class="text-muted" style="font-size:0.82rem">{{ username }}</span>
      </div>

      <div class="content-area">
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
const username = localStorage.getItem("username") || "Patient";

const pageTitle = computed(() => {
  const path = route.path;
  if (path === "/patient") return "Dashboard";
  if (path.includes("appointments")) return "My Appointments";
  if (path.includes("history")) return "Visit History";
  if (path.includes("profile")) return "My Profile";
  if (path.includes("export")) return "Export Data";
  return "Patient Portal";
});

const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  router.push("/login");
};
</script>
