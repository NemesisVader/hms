<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const profile = ref(null);
const loading = ref(true);
const editing = ref(false);
const editForm = ref({});
const message = ref("");

const fetchProfile = async () => {
  loading.value = true;
  try {
    const res = await api.get("/patient/me");
    profile.value = res.data;
    editForm.value = { ...res.data };
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const saveProfile = async () => {
  message.value = "";
  try {
    await api.put("/patient/me", {
      username: editForm.value.username,
      age: parseInt(editForm.value.age),
      gender: editForm.value.gender,
      phone: editForm.value.phone,
      address: editForm.value.address,
    });
    message.value = "Profile updated successfully!";
    editing.value = false;
    localStorage.setItem("username", editForm.value.username);
    fetchProfile();
    setTimeout(() => message.value = "", 3000);
  } catch (e) {
    message.value = e.response?.data?.msg || "Update failed";
  }
};

onMounted(fetchProfile);
</script>

<template>
  <div>
    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="profile" style="max-width:550px">
      <div class="section-header">
        <h4>My Profile</h4>
        <button v-if="!editing" class="btn btn-primary btn-sm" @click="editing = true">Edit</button>
      </div>

      <div v-if="message" class="alert" :class="message.includes('success') ? 'alert-success' : 'alert-danger'" style="font-size:0.85rem">
        {{ message }}
      </div>

      <div class="card">
        <div class="card-body">
          <div v-if="!editing">
            <div class="mb-3">
              <small class="text-muted">Username</small>
              <div class="fw-semibold">{{ profile.username }}</div>
            </div>
            <div class="row g-3">
              <div class="col-6">
                <small class="text-muted">Age</small>
                <div class="fw-semibold">{{ profile.age }}</div>
              </div>
              <div class="col-6">
                <small class="text-muted">Gender</small>
                <div class="fw-semibold">{{ profile.gender }}</div>
              </div>
              <div class="col-6">
                <small class="text-muted">Phone</small>
                <div class="fw-semibold">{{ profile.phone || '-' }}</div>
              </div>
              <div class="col-6">
                <small class="text-muted">Address</small>
                <div class="fw-semibold">{{ profile.address || '-' }}</div>
              </div>
            </div>
          </div>

          <div v-else>
            <div class="mb-3">
              <label class="form-label">Username</label>
              <input v-model="editForm.username" class="form-control" />
            </div>
            <div class="row g-3 mb-3">
              <div class="col-6">
                <label class="form-label">Age</label>
                <input v-model="editForm.age" type="number" class="form-control" />
              </div>
              <div class="col-6">
                <label class="form-label">Gender</label>
                <select v-model="editForm.gender" class="form-select">
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Phone</label>
              <input v-model="editForm.phone" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Address</label>
              <textarea v-model="editForm.address" class="form-control" rows="2"></textarea>
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-primary" @click="saveProfile">Save</button>
              <button class="btn btn-secondary" @click="editing = false">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
