<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const doctors = ref([]);
const departments = ref([]);
const loading = ref(true);
const error = ref(null);
const total = ref(0);
const searchQuery = ref("");
const showAddModal = ref(false);
const showEditModal = ref(false);

const newDoc = ref({ username: "", password: "", specialization: "", department_id: "", email: "", availability: {} });
const editDoc = ref({ doctor_id: null, username: "", specialization: "", department_id: "", email: "", availability: {} });
const showNewPassword = ref(false);
const addError = ref("");
const editError = ref("");

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

// Availability helpers
const addSlot = (avail, day) => {
  if (!avail[day]) avail[day] = [];
  avail[day].push("");
};
const removeSlot = (avail, day, idx) => {
  avail[day].splice(idx, 1);
  if (avail[day].length === 0) delete avail[day];
};
const addDay = (avail) => {
  const unused = DAYS.find(d => !avail[d]);
  if (unused) avail[unused] = [""];
};

const fetchDoctors = async () => {
  loading.value = true;
  try {
    const res = await api.get("/admin/doctors");
    doctors.value = res.data.items;
    total.value = res.data.total;
  } catch (e) { error.value = "Failed to load doctors"; }
  finally { loading.value = false; }
};

const fetchDepartments = async () => {
  try {
    const res = await api.get("/admin/departments");
    departments.value = res.data;
  } catch (e) { console.error(e); }
};

const searchDoctors = async () => {
  if (!searchQuery.value.trim()) { fetchDoctors(); return; }
  loading.value = true;
  try {
    const res = await api.get("/admin/doctors/search", { params: { q: searchQuery.value } });
    doctors.value = res.data;
    total.value = res.data.length;
  } catch (e) { error.value = "Search failed"; }
  finally { loading.value = false; }
};

const addDoctor = async () => {
  addError.value = "";
  if (!newDoc.value.username.trim()) { addError.value = "Username is required."; return; }
  if (!newDoc.value.password) { addError.value = "Password is required."; return; }
  if (!newDoc.value.email.trim()) { addError.value = "Email is required."; return; }
  if (!newDoc.value.specialization.trim()) { addError.value = "Specialization is required."; return; }
  if (!newDoc.value.department_id) { addError.value = "Please select a department."; return; }
  try {
    await api.post("/admin/doctors", newDoc.value);
    showAddModal.value = false;
    newDoc.value = { username: "", password: "", specialization: "", department_id: "", email: "", availability: {} };
    addError.value = "";
    fetchDoctors();
  } catch (e) {
    addError.value = e.response?.data?.msg || "Failed to add doctor";
  }
};

const openEdit = (doc) => {
  const dept = departments.value.find(d => d.name === doc.department);
  const availCopy = JSON.parse(JSON.stringify(doc.availability || {}));
  editDoc.value = {
    doctor_id: doc.doctor_id,
    username: doc.name || "",
    specialization: doc.specialization,
    department_id: dept ? dept.id : "",
    email: doc.email || "",
    availability: availCopy
  };
  editError.value = "";
  showEditModal.value = true;
};

const updateDoctor = async () => {
  editError.value = "";
  if (!editDoc.value.username.trim()) { editError.value = "Name is required."; return; }
  if (!editDoc.value.specialization.trim()) { editError.value = "Specialization is required."; return; }
  if (!editDoc.value.department_id) { editError.value = "Please select a department."; return; }
  try {
    await api.put(`/admin/doctors/${editDoc.value.doctor_id}`, {
      username: editDoc.value.username,
      specialization: editDoc.value.specialization,
      department_id: editDoc.value.department_id,
      email: editDoc.value.email,
      availability: editDoc.value.availability,
    });
    showEditModal.value = false;
    editError.value = "";
    fetchDoctors();
  } catch (e) {
    editError.value = e.response?.data?.msg || "Failed to update";
  }
};

const deleteDoctor = async (id) => {
  if (!confirm("Are you sure you want to blacklist this doctor? They will not be able to log in.")) return;
  try {
    await api.delete("/admin/doctors/" + id);
    fetchDoctors();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to blacklist doctor.");
  }
};

const restoreDoctor = async (id) => {
  try {
    await api.put("/admin/doctors/" + id + "/restore");
    fetchDoctors();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed to restore doctor.");
  }
};

onMounted(() => {
  fetchDoctors();
  fetchDepartments();
});
</script>

<template>
  <div>
    <div class="section-header">
      <h4>Doctors ({{ total }})</h4>
      <div class="d-flex gap-2">
        <div class="search-bar">
          <input
            v-model="searchQuery"
            class="form-control"
            placeholder="Search doctors..."
            style="min-width:200px"
            @input="searchDoctors"
          />
        </div>
        <button class="btn btn-primary" @click="showAddModal = true">+ Add Doctor</button>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else-if="doctors.length === 0" class="empty-state">
      <p>No doctors found.</p>
    </div>

    <div v-else class="card">
      <div class="card-body p-0">
        <table class="table table-hover mb-0">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Specialization</th>
              <th>Department</th>
              <th>Email</th>
              <th>Availability</th>
              <th>Status</th>
              <th style="width:200px">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="doc in doctors" :key="doc.doctor_id">
              <td>{{ doc.doctor_id }}</td>
              <td class="fw-semibold">{{ doc.name }}</td>
              <td>{{ doc.specialization }}</td>
              <td><span class="badge bg-light text-dark border">{{ doc.department }}</span></td>
              <td style="font-size:0.82rem">{{ doc.email || '—' }}</td>
              <td>
                <div v-if="doc.availability && Object.keys(doc.availability).length">
                  <span v-for="(times, day) in doc.availability" :key="day" class="slot-chip me-1">
                    {{ day }}: {{ times.length }}
                  </span>
                </div>
                <span v-else class="text-muted">Not set</span>
              </td>
              <td>
                <span v-if="doc.is_active" class="badge" style="background:#d1fae5;color:#16a34a">Active</span>
                <span v-else class="badge" style="background:#fee2e2;color:#dc2626">Blacklisted</span>
              </td>
              <td>
                <button class="btn btn-sm btn-outline-primary me-1" @click="openEdit(doc)">Edit</button>
                <button v-if="doc.is_active" class="btn btn-sm btn-outline-danger" @click.stop="deleteDoctor(doc.doctor_id)">Blacklist</button>
                <button v-else class="btn btn-sm btn-outline-success" @click.stop="restoreDoctor(doc.doctor_id)">Restore</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showAddModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add New Doctor</h5>
            <button class="btn-close" @click="showAddModal = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="addError" class="alert alert-danger py-2 mb-3" style="font-size:0.85rem">{{ addError }}</div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Username (Login ID) <span class="text-danger">*</span></label>
              <input v-model="newDoc.username" class="form-control" placeholder="doctor_username" required />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Password <span class="text-danger">*</span></label>
              <div class="input-group">
                <input v-model="newDoc.password" :type="showNewPassword ? 'text' : 'password'" class="form-control" placeholder="Password" required />
                <button class="btn btn-outline-secondary" type="button" @click="showNewPassword = !showNewPassword" style="border-color:var(--border);background:#fff">
                  <svg v-if="!showNewPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0z"/><path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8zm8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M13.359 11.238C15.06 9.72 16 8 16 8s-3-5.5-8-5.5a7.028 7.028 0 0 0-2.79.588l.77.771A5.944 5.944 0 0 1 8 3.5c2.12 0 3.879 1.168 5.168 2.457A13.134 13.134 0 0 1 14.828 8c-.058.087-.122.183-.195.288-.335.48-.83 1.12-1.465 1.755-.165.165-.337.328-.517.486l.708.709z"/><path d="M11.297 9.176a3.5 3.5 0 0 0-4.474-4.474l.823.823a2.5 2.5 0 0 1 2.829 2.829l.822.822zm-2.943 1.299l.822.822a3.5 3.5 0 0 1-4.474-4.474l.823.823a2.5 2.5 0 0 0 2.829 2.829z"/><path d="M3.35 5.47c-.18.16-.353.322-.518.487A13.134 13.134 0 0 0 1.172 8l.195.288c.335.48.83 1.12 1.465 1.755C4.121 11.332 5.881 12.5 8 12.5c.716 0 1.39-.133 2.02-.36l.77.772A7.029 7.029 0 0 1 8 13.5C3 13.5 0 8 0 8s.939-1.721 2.641-3.238l.708.709z"/><path d="M13.646 14.354l-12-12 .708-.708 12 12-.708.708z"/></svg>
                </button>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Email <span class="text-danger">*</span></label>
              <input v-model="newDoc.email" type="email" class="form-control" placeholder="doctor@hospital.com" required />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Specialization <span class="text-danger">*</span></label>
              <input v-model="newDoc.specialization" class="form-control" placeholder="e.g. Cardiologist" required />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Department <span class="text-danger">*</span></label>
              <select v-model="newDoc.department_id" class="form-select" required>
                <option value="" disabled>Select department</option>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <!-- Availability -->
            <div class="mb-3">
              <label class="form-label">Availability</label>
              <div v-for="(slots, day) in newDoc.availability" :key="day" class="mb-2 p-2 border rounded" style="background:#f8f9fa">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <strong style="font-size:0.85rem">{{ day }}</strong>
                  <button class="btn btn-sm btn-outline-danger" type="button" @click="delete newDoc.availability[day]">&times;</button>
                </div>
                <div v-for="(slot, idx) in slots" :key="idx" class="d-flex gap-2 mb-1">
                  <input v-model="slots[idx]" class="form-control form-control-sm" placeholder="e.g. 09:00-12:00" />
                  <button class="btn btn-sm btn-outline-secondary" type="button" @click="removeSlot(newDoc.availability, day, idx)">&minus;</button>
                </div>
                <button class="btn btn-sm btn-outline-primary mt-1" type="button" @click="addSlot(newDoc.availability, day)">+ Slot</button>
              </div>
              <button class="btn btn-sm btn-outline-secondary" type="button" @click="addDay(newDoc.availability)">+ Add Day</button>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
            <button class="btn btn-primary" @click="addDoctor">Add Doctor</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showEditModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Doctor #{{ editDoc.doctor_id }}</h5>
            <button class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <div v-if="editError" class="alert alert-danger py-2 mb-3" style="font-size:0.85rem">{{ editError }}</div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Name <span class="text-danger">*</span></label>
              <input v-model="editDoc.username" class="form-control" placeholder="Doctor name" required />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Email</label>
              <input v-model="editDoc.email" type="email" class="form-control" placeholder="doctor@hospital.com" />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Specialization <span class="text-danger">*</span></label>
              <input v-model="editDoc.specialization" class="form-control" required />
            </div>
            <div class="mb-3">
              <label class="form-label fw-semibold">Department <span class="text-danger">*</span></label>
              <select v-model="editDoc.department_id" class="form-select" required>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <!-- Availability Editor -->
            <div class="mb-3">
              <label class="form-label">Availability</label>
              <div v-for="(slots, day) in editDoc.availability" :key="day" class="mb-2 p-2 border rounded" style="background:#f8f9fa">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <strong style="font-size:0.85rem">{{ day }}</strong>
                  <button class="btn btn-sm btn-outline-danger" type="button" @click="delete editDoc.availability[day]">&times;</button>
                </div>
                <div v-for="(slot, idx) in slots" :key="idx" class="d-flex gap-2 mb-1">
                  <input v-model="slots[idx]" class="form-control form-control-sm" placeholder="e.g. 09:00-12:00" />
                  <button class="btn btn-sm btn-outline-secondary" type="button" @click="removeSlot(editDoc.availability, day, idx)">&minus;</button>
                </div>
                <button class="btn btn-sm btn-outline-primary mt-1" type="button" @click="addSlot(editDoc.availability, day)">+ Slot</button>
              </div>
              <button class="btn btn-sm btn-outline-secondary" type="button" @click="addDay(editDoc.availability)">+ Add Day</button>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
            <button class="btn btn-primary" @click="updateDoctor">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>