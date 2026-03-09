<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../api/axios";

const router = useRouter();

const form = ref({
  name: "",
  username: "",
  password: "",
  confirmPassword: "",
  age: "",
  gender: "",
  phone: "",
  address: "",
});

const error = ref(null);
const loading = ref(false);
const showPassword = ref(false);
const showConfirm = ref(false);

const register = async () => {
  error.value = null;

  if (!form.value.name || !form.value.name.trim()) {
    error.value = "Full name is required";
    return;
  }
  if (!form.value.username || !form.value.password) {
    error.value = "Username and password are required";
    return;
  }
  if (form.value.username.trim().length < 3) {
    error.value = "Username must be at least 3 characters";
    return;
  }
  if (form.value.password.length < 6) {
    error.value = "Password must be at least 6 characters";
    return;
  }
  if (form.value.password !== form.value.confirmPassword) {
    error.value = "Passwords do not match";
    return;
  }
  if (!form.value.age || !form.value.gender) {
    error.value = "Age and gender are required";
    return;
  }
  const ageNum = parseInt(form.value.age);
  if (isNaN(ageNum) || ageNum < 1 || ageNum > 120) {
    error.value = "Age must be a number between 1 and 120";
    return;
  }
  if (!form.value.phone || !form.value.phone.trim()) {
    error.value = "Phone number is required";
    return;
  }
  if (!/^[0-9+\-\s]{7,15}$/.test(form.value.phone.trim())) {
    error.value = "Enter a valid phone number (7–15 digits)";
    return;
  }

  loading.value = true;
  try {
    await api.post("/auth/register", {
      name: form.value.name,
      username: form.value.username,
      password: form.value.password,
      age: parseInt(form.value.age),
      gender: form.value.gender,
      phone: form.value.phone,
      address: form.value.address,
    });
    router.push("/login");
  } catch (err) {
    error.value = err.response?.data?.msg || "Registration failed";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="auth-wrapper">
    <div class="auth-card" style="max-width:440px">
      <h3>Patient Registration</h3>
      <p class="subtitle">Create your account</p>

      <div v-if="error" class="alert alert-danger py-2" style="font-size:0.85rem">
        {{ error }}
      </div>

      <div class="row g-3">
        <div class="col-12">
          <label class="form-label">Full Name <span class="text-danger">*</span></label>
          <input v-model="form.name" class="form-control" placeholder="Enter your full name" required />
        </div>

        <div class="col-12">
          <label class="form-label">Username <span class="text-danger">*</span></label>
          <input v-model="form.username" class="form-control" placeholder="Choose a username (min 3 chars)" required minlength="3" />
        </div>

        <div class="col-6">
          <label class="form-label">Password <span class="text-danger">*</span></label>
          <div class="input-group">
            <input v-model="form.password" :type="showPassword ? 'text' : 'password'" class="form-control" placeholder="Password (min 6 chars)" required minlength="6" />
            <button class="btn btn-outline-secondary" type="button" @click="showPassword = !showPassword" style="border-color:var(--border);background:#fff">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 0 0-2.79.588l.77.771A5.944 5.944 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829l.822.822zm-2.943 1.299l.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829z"/><path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709z"/><path d="M13.646 14.354l-12-12 .708-.708 12 12-.708.708z"/></svg>
            </button>
          </div>
        </div>
        <div class="col-6">
          <label class="form-label">Confirm Password <span class="text-danger">*</span></label>
          <div class="input-group">
            <input v-model="form.confirmPassword" :type="showConfirm ? 'text' : 'password'" class="form-control" placeholder="Confirm" required />
            <button class="btn btn-outline-secondary" type="button" @click="showConfirm = !showConfirm" style="border-color:var(--border);background:#fff">
              <svg v-if="!showConfirm" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 0 0-2.79.588l.77.771A5.944 5.944 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829l.822.822zm-2.943 1.299l.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829z"/><path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709z"/><path d="M13.646 14.354l-12-12 .708-.708 12 12-.708.708z"/></svg>
            </button>
          </div>
        </div>

        <div class="col-6">
          <label class="form-label">Age <span class="text-danger">*</span></label>
          <input v-model="form.age" type="number" class="form-control" placeholder="Age" min="1" max="120" required />
        </div>
        <div class="col-6">
          <label class="form-label">Gender <span class="text-danger">*</span></label>
          <select v-model="form.gender" class="form-select" required>
            <option value="" disabled>Select</option>
            <option value="Male">Male</option>
            <option value="Female">Female</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div class="col-12">
          <label class="form-label">Phone <span class="text-danger">*</span></label>
          <input v-model="form.phone" type="tel" class="form-control" placeholder="e.g. 9876543210" required pattern="[0-9+\-\s]{7,15}" />
        </div>

        <div class="col-12">
          <label class="form-label">Address</label>
          <textarea v-model="form.address" class="form-control" rows="2" placeholder="Your address"></textarea>
        </div>

        <div class="col-12">
          <button class="btn btn-primary w-100" @click="register" :disabled="loading">
            {{ loading ? "Registering..." : "Create Account" }}
          </button>
        </div>
      </div>

      <p class="text-center mt-3 mb-0" style="font-size:0.85rem">
        Already have an account?
        <router-link to="/login" class="text-decoration-none">Sign in</router-link>
      </p>
    </div>
  </div>
</template>