import { createRouter, createWebHistory } from 'vue-router'

// Auth views
import Login from '@/views/auth/Login.vue'
import Register from '@/views/auth/Register.vue'

// Home / Landing
import Home from '@/views/Home.vue'

// Admin views
import AdminDashboard from '@/views/admin/Dashboard.vue'
import AdminDoctors from '@/views/admin/Doctors.vue'
import AdminPatients from '@/views/admin/Patients.vue'
import AdminAppointments from '@/views/admin/Appointments.vue'
import AdminDepartments from '@/views/admin/Departments.vue'

// Doctor views
import DoctorDashboard from '@/views/doctor/Dashboard.vue'
import DoctorAppointments from '@/views/doctor/Appointments.vue'
import DoctorAvailability from '@/views/doctor/Availability.vue'
import DoctorPatients from '@/views/doctor/Patients.vue'
import DoctorPatientHistory from '@/views/doctor/PatientHistory.vue'

// Patient views
import PatientDashboard from '@/views/patient/Dashboard.vue'
import PatientAppointments from '@/views/patient/Appointments.vue'
import PatientHistory from '@/views/patient/History.vue'
import PatientProfile from '@/views/patient/Profile.vue'
import PatientExport from '@/views/patient/Export.vue'

// Layout wrappers
import AdminLayout from '@/components/layouts/AdminLayout.vue'
import DoctorLayout from '@/components/layouts/DoctorLayout.vue'
import PatientLayout from '@/components/layouts/PatientLayout.vue'

const routes = [
  { path: '/', component: Home, name: 'Home' },
  { path: '/login', component: Login, name: 'Login' },
  { path: '/register', component: Register, name: 'Register' },

  // Admin routes
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, role: 'admin' },
    children: [
      { path: '', redirect: '/admin/dashboard' },
      { path: 'dashboard', component: AdminDashboard, name: 'AdminDashboard' },
      { path: 'doctors', component: AdminDoctors, name: 'AdminDoctors' },
      { path: 'patients', component: AdminPatients, name: 'AdminPatients' },
      { path: 'appointments', component: AdminAppointments, name: 'AdminAppointments' },
      { path: 'departments', component: AdminDepartments, name: 'AdminDepartments' },
    ],
  },

  // Doctor routes
  {
    path: '/doctor',
    component: DoctorLayout,
    meta: { requiresAuth: true, role: 'doctor' },
    children: [
      { path: '', redirect: '/doctor/dashboard' },
      { path: 'dashboard', component: DoctorDashboard, name: 'DoctorDashboard' },
      { path: 'appointments', component: DoctorAppointments, name: 'DoctorAppointments' },
      { path: 'availability', component: DoctorAvailability, name: 'DoctorAvailability' },
      { path: 'patients', component: DoctorPatients, name: 'DoctorPatients' },
      { path: 'patient/:id', component: DoctorPatientHistory, name: 'DoctorPatientHistory' },
    ],
  },

  // Patient routes
  {
    path: '/patient',
    component: PatientLayout,
    meta: { requiresAuth: true, role: 'patient' },
    children: [
      { path: '', redirect: '/patient/dashboard' },
      { path: 'dashboard', component: PatientDashboard, name: 'PatientDashboard' },
      { path: 'appointments', component: PatientAppointments, name: 'PatientAppointments' },
      { path: 'history', component: PatientHistory, name: 'PatientHistory' },
      { path: 'profile', component: PatientProfile, name: 'PatientProfile' },
      { path: 'export', component: PatientExport, name: 'PatientExport' },
    ],
  },

  // Catch-all
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard — enforce role-based access
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (to.meta.requiresAuth) {
    if (!token) {
      return next('/login')
    }
    if (to.meta.role && to.meta.role !== role) {
      // Redirect to the user's own dashboard
      return next('/' + role)
    }
  }

  // Prevent logged-in users from accessing login/register
  if ((to.name === 'Login' || to.name === 'Register') && token) {
    return next('/' + role)
  }

  next()
})

export default router
