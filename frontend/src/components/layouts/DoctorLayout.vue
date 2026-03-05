<template>
  <div class="d-flex">
    <div class="sidebar p-0" style="width: 220px;">
      <div class="sidebar-brand">HMS Doctor</div>

      <div class="sidebar-nav">
        <router-link to="/doctor">Dashboard</router-link>
        <router-link to="/doctor/appointments">Appointments</router-link>
        <router-link to="/doctor/patients">My Patients</router-link>
        <router-link to="/doctor/availability">Availability</router-link>
      </div>

      <div class="sidebar-footer">
        <button class="btn btn-sm btn-outline-light w-100" @click="logout">Logout</button>
      </div>
    </div>

    <div class="flex-fill" style="min-width:0">
      <div class="top-header">
        <h5>{{ pageTitle }}</h5>
        <span class="text-muted" style="font-size:0.82rem">Dr. {{ username }}</span>
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
const username = localStorage.getItem("username") || "Doctor";

const pageTitle = computed(() => {
  const path = route.path;
  if (path === "/doctor") return "Dashboard";
  if (path.includes("appointments")) return "My Appointments";
  if (path === "/doctor/patients") return "My Patients";
  if (path.includes("patient")) return "Patient History";
  if (path.includes("availability")) return "Set Availability";
  return "Doctor Panel";
});

const logout = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  router.push("/login");
};
</script>
