<script setup>
import { ref, onMounted, computed } from "vue";
import api from "../../api/axios";

const availability = ref({});
const loading = ref(true);
const saving = ref(false);
const message = ref("");

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const timeSlots = [
  "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
  "12:00", "12:30", "14:00", "14:30", "15:00", "15:30",
  "16:00", "16:30", "17:00", "17:30"
];

const toggleSlot = (day, time) => {
  if (!availability.value[day]) {
    availability.value[day] = [];
  }
  const idx = availability.value[day].indexOf(time);
  if (idx === -1) {
    availability.value[day].push(time);
    availability.value[day].sort();
  } else {
    availability.value[day].splice(idx, 1);
  }
};

const isActive = (day, time) => {
  return availability.value[day] && availability.value[day].includes(time);
};

const totalSlots = computed(() => {
  return Object.values(availability.value).reduce((sum, slots) => sum + slots.length, 0);
});

const saveAvailability = async () => {
  saving.value = true;
  message.value = "";
  try {
    await api.put("/doctor/availability", { availability: availability.value });
    message.value = "Availability saved successfully!";
    setTimeout(() => message.value = "", 3000);
  } catch (e) {
    message.value = e.response?.data?.msg || "Failed to save";
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  try {
    const res = await api.get("/doctor/availability");
    if (res.data && res.data.availability) {
      availability.value = res.data.availability;
    }
  } catch (e) {
    // No existing availability — doctor starts fresh
    console.log("No existing availability loaded");
  }
  loading.value = false;
});
</script>

<template>
  <div>
    <div class="section-header">
      <h4>Set Your Availability</h4>
      <div class="d-flex align-items-center gap-3">
        <span class="text-muted" style="font-size:0.85rem">{{ totalSlots }} slots selected</span>
        <button class="btn btn-primary" @click="saveAvailability" :disabled="saving">
          {{ saving ? "Saving..." : "Save Availability" }}
        </button>
      </div>
    </div>

    <div v-if="message" class="alert" :class="message.includes('success') ? 'alert-success' : 'alert-danger'" style="font-size:0.85rem">
      {{ message }}
    </div>

    <p class="text-muted mb-3" style="font-size:0.85rem">
      Click on time slots to toggle availability for each day.
    </p>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else class="row g-3">
      <div v-for="day in days" :key="day" class="col-md-6 col-lg-4 col-xl-3">
        <div class="avail-day">
          <div class="day-name">{{ day }}</div>
          <div class="d-flex flex-wrap gap-1">
            <span
              v-for="time in timeSlots"
              :key="time"
              class="slot-chip"
              :class="{ active: isActive(day, time) }"
              @click="toggleSlot(day, time)"
            >
              {{ time }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
