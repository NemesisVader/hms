<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import api from "../../api/axios";

const router = useRouter();

const username = ref("");
const password = ref("");
const error = ref(null);
const loading = ref(false);
const showPassword = ref(false);

const login = async () => {
  error.value = null;
  loading.value = true;

  try {
    const response = await api.post("/auth/login", {
      username: username.value,
      password: password.value,
    });

    const token = response.data.access_token;
    localStorage.setItem("token", token);

    const me = await api.get("/auth/me");
    const role = me.data.role;
    localStorage.setItem("role", role);
    localStorage.setItem("username", me.data.username);

    if (role === "admin") router.push("/admin");
    else if (role === "doctor") router.push("/doctor");
    else if (role === "patient") router.push("/patient");
  } catch (err) {
    error.value = err.response?.data?.msg || "Invalid credentials";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="auth-wrapper">
    <div class="auth-card">
      <h3>Hospital Management</h3>
      <p class="subtitle">Sign in to your account</p>

      <div v-if="error" class="alert alert-danger py-2" style="font-size:0.85rem">
        {{ error }}
      </div>

      <div class="mb-3">
        <label class="form-label">Username</label>
        <input
          v-model="username"
          class="form-control"
          placeholder="Enter username"
          @keyup.enter="login"
        />
      </div>

      <div class="mb-3">
        <label class="form-label">Password</label>
        <div class="input-group">
          <input
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            class="form-control"
            placeholder="Enter password"
            @keyup.enter="login"
          />
          <button class="btn btn-outline-secondary" type="button" @click="showPassword = !showPassword" style="border-color:var(--border);background:#fff">
            <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 0 0-2.79.588l.77.771A5.944 5.944 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829l.822.822zm-2.943 1.299l.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829z"/><path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709z"/><path d="M13.646 14.354l-12-12 .708-.708 12 12-.708.708z"/></svg>
          </button>
        </div>
      </div>

      <button
        class="btn btn-primary w-100"
        @click="login"
        :disabled="loading"
      >
        {{ loading ? "Signing in..." : "Sign In" }}
      </button>

      <p class="text-center mt-3 mb-0" style="font-size:0.85rem">
        New patient?
        <router-link to="/register" class="text-decoration-none">Register here</router-link>
      </p>
    </div>
  </div>
</template>