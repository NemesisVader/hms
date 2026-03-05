<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const patients = ref([]);
const loading = ref(true);
const total = ref(0);
const searchQuery = ref("");
const showEditModal = ref(false);
const showAddModal = ref(false);
const editPat = ref({});
const newPat = ref({ username: "", password: "", age: "", gender: "", phone: "", address: "" });
const showNewPassword = ref(false);

const fetchPatients = async () => {
  loading.value = true;
  try {
    const res = await api.get("/admin/patients");
    patients.value = res.data.items;
    total.value = res.data.total;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const searchPatients = async () => {
  if (!searchQuery.value.trim()) { fetchPatients(); return; }
  loading.value = true;
  try {
    const res = await api.get("/admin/patients/search", { params: { q: searchQuery.value } });
    patients.value = res.data;
    total.value = res.data.length;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const addPatient = async () => {
  try {
    await api.post("/auth/register", {
      username: newPat.value.username,
      password: newPat.value.password,
      age: parseInt(newPat.value.age),
      gender: newPat.value.gender,
      phone: newPat.value.phone,
      address: newPat.value.address,
    });
    showAddModal.value = false;
    newPat.value = { username: "", password: "", age: "", gender: "", phone: "", address: "" };
    fetchPatients();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to add patient");
  }
};

const openEdit = (p) => {
  editPat.value = { ...p };
  showEditModal.value = true;
};

const updatePatient = async () => {
  try {
    await api.put("/admin/patients/" + editPat.value.patient_id, {
      username: editPat.value.name,
      age: editPat.value.age,
      gender: editPat.value.gender,
      phone: editPat.value.phone,
      address: editPat.value.address,
    });
    showEditModal.value = false;
    fetchPatients();
  } catch (e) {
    alert(e.response?.data?.msg || "Update failed");
  }
};

const deletePatient = async (id) => {
  if (!confirm("Are you sure you want to blacklist this patient? They will not be able to log in.")) return;
  try {
    await api.delete("/admin/patients/" + id);
    fetchPatients();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to blacklist patient.");
  }
};

const restorePatient = async (id) => {
  try {
    await api.put("/admin/patients/" + id + "/restore");
    fetchPatients();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to restore patient.");
  }
};

onMounted(fetchPatients);
</script>

<template>
  <div>
    <div class="section-header">
      <h4>Patients ({{ total }})</h4>
      <div class="d-flex gap-2">
        <div class="search-bar">
          <input
            v-model="searchQuery"
            class="form-control"
            placeholder="Search by name, phone, or ID..."
            style="min-width:220px"
            @input="searchPatients"
          />
        </div>
        <button class="btn btn-primary" @click="showAddModal = true">+ Add Patient</button>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="patients.length === 0" class="empty-state">
      <p>No patients found.</p>
    </div>

    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Age</th>
              <th>Gender</th>
              <th>Phone</th>
              <th>Address</th>
              <th>Status</th>
              <th style="width:200px">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in patients" :key="p.patient_id">
              <td>{{ p.patient_id }}</td>
              <td class="fw-semibold">{{ p.name }}</td>
              <td>{{ p.age }}</td>
              <td>{{ p.gender }}</td>
              <td>{{ p.phone || '-' }}</td>
              <td>{{ p.address || '-' }}</td>
              <td>
                <span v-if="p.is_active" class="badge" style="background:#d1fae5;color:#16a34a">Active</span>
                <span v-else class="badge" style="background:#fee2e2;color:#dc2626">Blacklisted</span>
              </td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(p)">Edit</button>
                <button v-if="p.is_active" class="btn btn-sm btn-outline-danger" @click.stop="deletePatient(p.patient_id)">Blacklist</button>
                <button v-else class="btn btn-sm btn-outline-success" @click.stop="restorePatient(p.patient_id)">Restore</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Patient Modal -->
    <div v-if="showAddModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showAddModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add New Patient</h5>
            <button class="btn-close" @click="showAddModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Username (Login ID)</label>
              <input v-model="newPat.username" class="form-control" placeholder="patient_username" />
            </div>
            <div class="mb-3">
              <label class="form-label">Password</label>
              <div class="input-group">
                <input v-model="newPat.password" :type="showNewPassword ? 'text' : 'password'" class="form-control" placeholder="Password" />
                <button class="btn btn-outline-secondary" type="button" @click="showNewPassword = !showNewPassword" style="border-color:var(--border);background:#fff">
                  <svg v-if="!showNewPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 0 0-2.79.588l.77.771A5.944 5.944 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829l.822.822zm-2.943 1.299l.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829z"/><path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709z"/><path d="M13.646 14.354l-12-12 .708-.708 12 12-.708.708z"/></svg>
                </button>
              </div>
            </div>
            <div class="row g-3 mb-3">
              <div class="col-6">
                <label class="form-label">Age</label>
                <input v-model="newPat.age" type="number" class="form-control" placeholder="Age" />
              </div>
              <div class="col-6">
                <label class="form-label">Gender</label>
                <select v-model="newPat.gender" class="form-select">
                  <option value="" disabled>Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Phone</label>
              <input v-model="newPat.phone" class="form-control" placeholder="Phone number" />
            </div>
            <div class="mb-3">
              <label class="form-label">Address</label>
              <textarea v-model="newPat.address" class="form-control" rows="2" placeholder="Address"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
            <button class="btn btn-primary" @click="addPatient">Add Patient</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showEditModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Patient #{{ editPat.patient_id }}</h5>
            <button class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Name</label>
              <input v-model="editPat.name" class="form-control" />
            </div>
            <div class="row g-3 mb-3">
              <div class="col-6">
                <label class="form-label">Age</label>
                <input v-model="editPat.age" type="number" class="form-control" />
              </div>
              <div class="col-6">
                <label class="form-label">Gender</label>
                <select v-model="editPat.gender" class="form-select">
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Phone</label>
              <input v-model="editPat.phone" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Address</label>
              <textarea v-model="editPat.address" class="form-control" rows="2"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
            <button class="btn btn-primary" @click="updatePatient">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>