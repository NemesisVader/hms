<script setup>
import { ref, onMounted } from "vue";
import api from "../../api/axios";

const departments = ref([]);
const loading = ref(true);
const searchQuery = ref("");
const showAddModal = ref(false);
const showEditModal = ref(false);

const newDept = ref({ name: "", description: "" });
const editDept = ref({ id: null, name: "", description: "" });

const fetchDepartments = async () => {
  loading.value = true;
  try {
    const res = await api.get("/admin/departments");
    departments.value = res.data;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const searchDepartments = async () => {
  if (!searchQuery.value.trim()) { fetchDepartments(); return; }
  loading.value = true;
  try {
    const res = await api.get("/admin/departments/search", { params: { q: searchQuery.value } });
    departments.value = res.data;
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
};

const addDepartment = async () => {
  try {
    await api.post("/admin/departments", newDept.value);
    showAddModal.value = false;
    newDept.value = { name: "", description: "" };
    fetchDepartments();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed");
  }
};

const openEdit = (d) => {
  editDept.value = { id: d.id, name: d.name, description: d.description };
  showEditModal.value = true;
};

const updateDepartment = async () => {
  try {
    await api.put("/admin/departments/" + editDept.value.id, {
      name: editDept.value.name,
      description: editDept.value.description,
    });
    showEditModal.value = false;
    fetchDepartments();
  } catch (e) {
    alert(e.response?.data?.msg || "Failed");
  }
};

const deleteDepartment = async (id) => {
  if (!confirm("Delete this department?")) return;
  try {
    await api.delete("/admin/departments/" + id);
    fetchDepartments();
  } catch (e) {
    alert(e.response?.data?.msg || "Cannot delete. Department may have doctors assigned.");
  }
};

onMounted(fetchDepartments);
</script>

<template>
  <div>
    <div class="section-header">
      <h4>Departments ({{ departments.length }})</h4>
      <div class="d-flex gap-2">
        <div class="search-bar">
          <input v-model="searchQuery" class="form-control" placeholder="Search departments..." style="min-width:200px" @input="searchDepartments" />
        </div>
        <button class="btn btn-primary" @click="showAddModal = true">+ Add</button>
      </div>
    </div>

    <div v-if="loading" class="loading-overlay">
      <div class="spinner-border text-primary"></div>
    </div>

    <div v-else class="row g-3">
      <div v-for="dept in departments" :key="dept.id" class="col-md-6 col-lg-4">
        <div class="card h-100">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="mb-0 fw-bold">{{ dept.name }}</h6>
              <div>
                <button class="btn btn-sm btn-outline-secondary me-1" @click="openEdit(dept)">Edit</button>
                <button class="btn btn-sm btn-outline-danger" @click.stop="deleteDepartment(dept.id)">Delete</button>
              </div>
            </div>
            <p class="text-muted mb-2" style="font-size:0.85rem">{{ dept.description || 'No description' }}</p>
            <span class="badge bg-light text-dark border">{{ dept.doctor_count || 0 }} Doctors</span>

            <div v-if="dept.doctors && dept.doctors.length" class="mt-3">
              <div v-for="doc in dept.doctors" :key="doc.doctor_id" class="d-flex align-items-center gap-2 py-1" style="font-size:0.82rem">
                <span class="fw-semibold">{{ doc.name }}</span>
                <span class="text-muted">- {{ doc.specialization }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Modal -->
    <div v-if="showAddModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showAddModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Add Department</h5>
            <button class="btn-close" @click="showAddModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Department Name</label>
              <input v-model="newDept.name" class="form-control" placeholder="e.g. Cardiology" />
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea v-model="newDept.description" class="form-control" rows="3" placeholder="Brief description"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showAddModal = false">Cancel</button>
            <button class="btn btn-primary" @click="addDepartment">Create</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Modal -->
    <div v-if="showEditModal" class="modal d-block" style="background:rgba(0,0,0,0.4)" @click.self="showEditModal = false">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">Edit Department</h5>
            <button class="btn-close" @click="showEditModal = false"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label">Name</label>
              <input v-model="editDept.name" class="form-control" />
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea v-model="editDept.description" class="form-control" rows="3"></textarea>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showEditModal = false">Cancel</button>
            <button class="btn btn-primary" @click="updateDepartment">Save</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
