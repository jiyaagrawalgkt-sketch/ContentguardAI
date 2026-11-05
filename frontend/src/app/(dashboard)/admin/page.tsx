"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import { AppNavbar } from "@/components/layout/AppNavbar";
import {
  Users,
  Building2,
  FileText,
  Clock,
  CheckCircle2,
  XCircle,
  BarChart3,
  ShieldAlert,
  Search,
  Plus,
  Loader2,
  AlertCircle,
  Activity,
  Server,
  Database,
  ArrowRight,
  UserCheck,
  UserX,
  X,
  RefreshCw,
  Sliders,
  Check
} from "lucide-react";

interface OverviewStats {
  total_users: number;
  total_organizations: number;
  total_submissions: number;
  pending_reviews: number;
  approved_publications: number;
  rejected_submissions: number;
  average_compliance_score: number;
}

interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id: string;
  organization_name?: string;
  is_active: boolean;
  created_at: string;
}

interface AdminOrg {
  id: string;
  name: string;
  slug: string;
  industry?: string;
  user_count: number;
  submission_count: number;
  guidelines_count: number;
  created_at: string;
}

interface SystemHealth {
  database_connected: boolean;
  database_type: string;
  total_records: Record<string, number>;
  environment: string;
  version: string;
}

interface ActivityLog {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  user_email?: string;
  user_name?: string;
  details?: any;
  created_at: string;
}

export default function AdminDashboardPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();

  const [activeTab, setActiveTab] = useState<"overview" | "users" | "orgs" | "monitoring">("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // Data states
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [usersList, setUsersList] = useState<AdminUser[]>([]);
  const [orgsList, setOrgsList] = useState<AdminOrg[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [activities, setActivities] = useState<ActivityLog[]>([]);

  // User Filter states
  const [userSearch, setUserSearch] = useState("");
  const [userRoleFilter, setUserRoleFilter] = useState("all");

  // Create User Modal
  const [showCreateUserModal, setShowCreateUserModal] = useState(false);
  const [newUserEmail, setNewUserEmail] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState("creator");
  const [newUserOrgId, setNewUserOrgId] = useState("");
  const [creatingUser, setCreatingUser] = useState(false);

  // Create Org Modal
  const [showCreateOrgModal, setShowCreateOrgModal] = useState(false);
  const [newOrgName, setNewOrgName] = useState("");
  const [newOrgIndustry, setNewOrgIndustry] = useState("Enterprise Cloud Software");
  const [creatingOrg, setCreatingOrg] = useState(false);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
      return;
    }

    if (isAuthenticated && user) {
      if (user.role !== "admin") {
        setError("Access Denied: You must be an administrator to access this dashboard.");
        setLoading(false);
        return;
      }
      loadDashboardData();
    }
  }, [isAuthenticated, authLoading, user, router]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsRes, usersRes, orgsRes, healthRes, actRes] = await Promise.all([
        api.get("/admin/overview"),
        api.get("/admin/users"),
        api.get("/admin/organizations"),
        api.get("/admin/system/health"),
        api.get("/admin/system/activity?limit=20"),
      ]);

      setStats(statsRes.data);
      setUsersList(usersRes.data);
      setOrgsList(orgsRes.data);
      setHealth(healthRes.data);
      setActivities(actRes.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load admin metrics.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRole = async (userId: string, newRole: string) => {
    try {
      setNotification(null);
      await api.put(`/admin/users/${userId}/role`, { role: newRole });
      setNotification({ type: "success", message: "User role updated successfully." });
      // Refresh list
      const res = await api.get("/admin/users");
      setUsersList(res.data);
    } catch (err: any) {
      setNotification({ type: "error", message: err.response?.data?.detail || "Failed to update role." });
    }
  };

  const handleToggleStatus = async (userId: string, currentStatus: boolean) => {
    try {
      setNotification(null);
      await api.put(`/admin/users/${userId}/status`, { is_active: !currentStatus });
      setNotification({
        type: "success",
        message: `User account ${!currentStatus ? "activated" : "deactivated"} successfully.`
      });
      const res = await api.get("/admin/users");
      setUsersList(res.data);
    } catch (err: any) {
      setNotification({ type: "error", message: err.response?.data?.detail || "Failed to update user status." });
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreatingUser(true);
      setNotification(null);
      await api.post("/admin/users", {
        email: newUserEmail,
        full_name: newUserName,
        password: newUserPassword,
        role: newUserRole,
        organization_id: newUserOrgId || undefined,
      });

      setNotification({ type: "success", message: `User '${newUserEmail}' created successfully.` });
      setShowCreateUserModal(false);
      setNewUserEmail("");
      setNewUserName("");
      setNewUserPassword("");

      // Refresh data
      const [uRes, sRes] = await Promise.all([api.get("/admin/users"), api.get("/admin/overview")]);
      setUsersList(uRes.data);
      setStats(sRes.data);
    } catch (err: any) {
      setNotification({ type: "error", message: err.response?.data?.detail || "Failed to create user." });
    } finally {
      setCreatingUser(false);
    }
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setCreatingOrg(true);
      setNotification(null);
      await api.post("/admin/organizations", {
        name: newOrgName,
        industry: newOrgIndustry,
      });

      setNotification({ type: "success", message: `Organization '${newOrgName}' created successfully.` });
      setShowCreateOrgModal(false);
      setNewOrgName("");

      // Refresh data
      const [oRes, sRes] = await Promise.all([api.get("/admin/organizations"), api.get("/admin/overview")]);
      setOrgsList(oRes.data);
      setStats(sRes.data);
    } catch (err: any) {
      setNotification({ type: "error", message: err.response?.data?.detail || "Failed to create organization." });
    } finally {
      setCreatingOrg(false);
    }
  };

  const filteredUsers = usersList.filter((u) => {
    const matchesSearch =
      u.full_name.toLowerCase().includes(userSearch.toLowerCase()) ||
      u.email.toLowerCase().includes(userSearch.toLowerCase());
    const matchesRole = userRoleFilter === "all" || u.role === userRoleFilter;
    return matchesSearch && matchesRole;
  });

  if (error && user?.role !== "admin") {
    return (
      <div className="min-h-screen bg-lavender-50 flex flex-col">
        <AppNavbar />
        <main className="flex-1 max-w-xl w-full mx-auto p-8 flex flex-col justify-center items-center text-center">
          <div className="p-8 bg-white rounded-3xl border border-rose-200 shadow-card">
            <ShieldAlert className="w-12 h-12 text-rose-500 mx-auto mb-3" />
            <h2 className="text-xl font-bold text-midnight-950 mb-2">Access Denied</h2>
            <p className="text-xs text-midnight-600 mb-6 leading-relaxed">{error}</p>
            <Link
              href={user?.role === "reviewer" ? "/reviewer" : "/creator"}
              className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 transition-all shadow-md"
            >
              <span>Go to Your Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-lavender-50 flex flex-col">
      <AppNavbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                Administration & Governance Console
              </span>
              <span className="text-xs text-midnight-500">• Production Multi-Tenant</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-midnight-950 tracking-tight">
              Enterprise Admin Center
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={loadDashboardData}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-white border border-midnight-200 text-midnight-700 hover:bg-lavender-50 transition-all shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5 text-midnight-500" />
              <span>Refresh Metrics</span>
            </button>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div
            className={`mb-6 p-4 rounded-2xl border flex items-center justify-between gap-3 text-xs ${
              notification.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-rose-50 border-rose-200 text-rose-800"
            }`}
          >
            <div className="flex items-center gap-2 font-medium">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{notification.message}</span>
            </div>
            <button onClick={() => setNotification(null)} className="p-1 hover:opacity-75">
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex items-center gap-2 border-b border-midnight-200/80 mb-6">
          <button
            onClick={() => setActiveTab("overview")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "overview"
                ? "border-midnight-950 text-midnight-950"
                : "border-transparent text-midnight-500 hover:text-midnight-900"
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Platform Overview</span>
          </button>

          <button
            onClick={() => setActiveTab("users")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "users"
                ? "border-midnight-950 text-midnight-950"
                : "border-transparent text-midnight-500 hover:text-midnight-900"
            }`}
          >
            <Users className="w-4 h-4" />
            <span>User Management ({usersList.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("orgs")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "orgs"
                ? "border-midnight-950 text-midnight-950"
                : "border-transparent text-midnight-500 hover:text-midnight-900"
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Organizations ({orgsList.length})</span>
          </button>

          <button
            onClick={() => setActiveTab("monitoring")}
            className={`pb-3 px-3 text-xs font-bold border-b-2 transition-all flex items-center gap-2 ${
              activeTab === "monitoring"
                ? "border-midnight-950 text-midnight-950"
                : "border-transparent text-midnight-500 hover:text-midnight-900"
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>System Monitoring</span>
          </button>
        </div>

        {/* Content Body */}
        {loading ? (
          <div className="py-24 flex flex-col items-center justify-center text-midnight-500">
            <Loader2 className="w-8 h-8 animate-spin text-emerald-600 mb-3" />
            <p className="text-sm">Querying real-time database metrics...</p>
          </div>
        ) : (
          <>
            {/* 1. OVERVIEW TAB */}
            {activeTab === "overview" && stats && (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3.5">
                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
                    <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider block mb-1">
                      Registered Users
                    </span>
                    <p className="text-2xl font-extrabold text-midnight-950">{stats.total_users}</p>
                    <span className="text-[10px] text-midnight-400">Total accounts</span>
                  </div>

                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
                    <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider block mb-1">
                      Organizations
                    </span>
                    <p className="text-2xl font-extrabold text-midnight-950">{stats.total_organizations}</p>
                    <span className="text-[10px] text-midnight-400">Tenants</span>
                  </div>

                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
                    <span className="text-[10px] font-bold text-midnight-500 uppercase tracking-wider block mb-1">
                      Total Submissions
                    </span>
                    <p className="text-2xl font-extrabold text-midnight-950">{stats.total_submissions}</p>
                    <span className="text-[10px] text-midnight-400">Drafts & copies</span>
                  </div>

                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
                    <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider block mb-1">
                      Pending Reviews
                    </span>
                    <p className="text-2xl font-extrabold text-amber-700">{stats.pending_reviews}</p>
                    <span className="text-[10px] text-amber-600">Awaiting sign-off</span>
                  </div>

                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
                    <span className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider block mb-1">
                      Approved Content
                    </span>
                    <p className="text-2xl font-extrabold text-emerald-700">{stats.approved_publications}</p>
                    <span className="text-[10px] text-emerald-600">Certified live</span>
                  </div>

                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card">
                    <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider block mb-1">
                      Rejected
                    </span>
                    <p className="text-2xl font-extrabold text-rose-700">{stats.rejected_submissions}</p>
                    <span className="text-[10px] text-rose-600">Non-compliant</span>
                  </div>

                  <div className="bg-white p-4 rounded-2xl border border-midnight-100 shadow-card col-span-2 md:col-span-1">
                    <span className="text-[10px] font-bold text-brand-700 uppercase tracking-wider block mb-1">
                      Avg Compliance
                    </span>
                    <p className="text-2xl font-extrabold text-brand-700 font-mono">
                      {stats.average_compliance_score.toFixed(0)}%
                    </p>
                    <span className="text-[10px] text-brand-600">Calculated score</span>
                  </div>
                </div>

                {/* System status pill card */}
                {health && (
                  <div className="p-5 rounded-2xl bg-white border border-midnight-100 shadow-card flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center">
                        <Database className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-bold text-midnight-950">Database Connection Active</p>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-bold font-mono">
                            {health.database_type}
                          </span>
                        </div>
                        <p className="text-[11px] text-midnight-500">
                          {health.total_records.users} users • {health.total_records.submissions} submissions •{" "}
                          {health.total_records.audit_logs} audit records logged
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-lavender-50 border border-midnight-100 text-midnight-700">
                      Release v{health.version} • Status: Operational
                    </span>
                  </div>
                )}

                {/* Recent Activity Mini-Feed */}
                <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden">
                  <div className="p-5 border-b border-midnight-100 flex items-center justify-between">
                    <h3 className="text-xs font-bold text-midnight-950 uppercase tracking-wider">
                      Recent Governance & Platform Activity
                    </h3>
                    <button
                      onClick={() => setActiveTab("monitoring")}
                      className="text-xs font-semibold text-brand-600 hover:text-brand-800 transition-colors"
                    >
                      View Full Audit Trail &rarr;
                    </button>
                  </div>
                  <div className="divide-y divide-midnight-100">
                    {activities.slice(0, 6).map((act) => (
                      <div key={act.id} className="p-4 flex items-center justify-between text-xs hover:bg-lavender-50/40">
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-lavender-100 text-midnight-800 border border-midnight-200">
                            {act.action}
                          </span>
                          <div>
                            <p className="font-semibold text-midnight-900">
                              {act.user_name || "System"} ({act.user_email || "system@contentguard"})
                            </p>
                            <p className="text-[11px] text-midnight-500">Target Entity: {act.entity_type}</p>
                          </div>
                        </div>
                        <span className="text-[11px] text-midnight-400 font-mono">
                          {new Date(act.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 2. USER MANAGEMENT TAB */}
            {activeTab === "users" && (
              <div className="space-y-4">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="flex items-center gap-2 w-full sm:w-auto">
                    <div className="relative w-full sm:w-72">
                      <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-midnight-400" />
                      <input
                        type="text"
                        placeholder="Search users by name or email..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        className="w-full pl-9 pr-3 py-2 rounded-xl text-xs border border-midnight-200 bg-white focus:outline-none focus:border-brand-500 shadow-sm"
                      />
                    </div>

                    <select
                      value={userRoleFilter}
                      onChange={(e) => setUserRoleFilter(e.target.value)}
                      className="text-xs border border-midnight-200 rounded-xl px-3 py-2 bg-white focus:outline-none focus:border-brand-500 shadow-sm"
                    >
                      <option value="all">All Roles</option>
                      <option value="creator">Creators</option>
                      <option value="reviewer">Reviewers</option>
                      <option value="admin">Admins</option>
                    </select>
                  </div>

                  <button
                    onClick={() => setShowCreateUserModal(true)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-midnight-900 text-white hover:bg-midnight-800 shadow-sm transition-all"
                  >
                    <Plus className="w-3.5 h-3.5 text-brand-400" />
                    <span>Create User</span>
                  </button>
                </div>

                <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs text-midnight-800">
                      <thead className="bg-lavender-50/60 border-b border-midnight-100 text-[10px] uppercase tracking-wider font-bold text-midnight-500">
                        <tr>
                          <th className="px-6 py-3.5">User</th>
                          <th className="px-6 py-3.5">Organization</th>
                          <th className="px-6 py-3.5">Assigned Role</th>
                          <th className="px-6 py-3.5">Account Status</th>
                          <th className="px-6 py-3.5">Created Date</th>
                          <th className="px-6 py-3.5 text-right">Role & Status Controls</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-midnight-100">
                        {filteredUsers.map((u) => (
                          <tr key={u.id} className="hover:bg-lavender-50/30 transition-colors">
                            <td className="px-6 py-4">
                              <p className="font-semibold text-midnight-950">{u.full_name}</p>
                              <p className="text-[11px] text-midnight-400 font-mono">{u.email}</p>
                            </td>

                            <td className="px-6 py-4">
                              <span className="font-medium text-midnight-700">{u.organization_name || "Unassigned"}</span>
                            </td>

                            <td className="px-6 py-4">
                              <span
                                className={`inline-block px-2.5 py-0.5 rounded-full font-bold text-[10px] uppercase tracking-wider ${
                                  u.role === "admin"
                                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                    : u.role === "reviewer"
                                    ? "bg-purple-50 text-purple-700 border border-purple-200"
                                    : "bg-blue-50 text-blue-700 border border-blue-200"
                                }`}
                              >
                                {u.role}
                              </span>
                            </td>

                            <td className="px-6 py-4">
                              <span
                                className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold ${
                                  u.is_active
                                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                    : "bg-rose-50 text-rose-700 border border-rose-200"
                                }`}
                              >
                                {u.is_active ? "Active" : "Deactivated"}
                              </span>
                            </td>

                            <td className="px-6 py-4 text-midnight-400 font-mono text-[11px]">
                              {new Date(u.created_at).toLocaleDateString()}
                            </td>

                            <td className="px-6 py-4 text-right">
                              <div className="inline-flex items-center gap-2">
                                {/* Change Role Selector */}
                                <select
                                  value={u.role}
                                  onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                                  className="text-[11px] border border-midnight-200 rounded-lg px-2 py-1 bg-white focus:outline-none"
                                >
                                  <option value="creator">Creator</option>
                                  <option value="reviewer">Reviewer</option>
                                  <option value="admin">Admin</option>
                                </select>

                                {/* Toggle Active/Deactivate Button */}
                                <button
                                  onClick={() => handleToggleStatus(u.id, u.is_active)}
                                  disabled={u.id === user?.id}
                                  title={u.id === user?.id ? "Cannot deactivate yourself" : "Toggle status"}
                                  className={`p-1.5 rounded-lg border transition-all text-xs ${
                                    u.is_active
                                      ? "text-rose-600 border-rose-200 hover:bg-rose-50 disabled:opacity-40"
                                      : "text-emerald-600 border-emerald-200 hover:bg-emerald-50"
                                  }`}
                                >
                                  {u.is_active ? <UserX className="w-3.5 h-3.5" /> : <UserCheck className="w-3.5 h-3.5" />}
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* 3. ORGANIZATIONS TAB */}
            {activeTab === "orgs" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <p className="text-xs text-midnight-600">
                    Manage tenant organizations, team membership counts, and guideline associations.
                  </p>
                  <button
                    onClick={() => setShowCreateOrgModal(true)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-midnight-900 text-white hover:bg-midnight-800 shadow-sm transition-all"
                  >
                    <Plus className="w-3.5 h-3.5 text-brand-400" />
                    <span>Create Organization</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {orgsList.map((org) => (
                    <div key={org.id} className="p-5 rounded-3xl bg-white border border-midnight-100 shadow-card flex flex-col justify-between">
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-lavender-100 text-midnight-700">
                            {org.slug}
                          </span>
                          <span className="text-[10px] text-midnight-400">
                            Created {new Date(org.created_at).toLocaleDateString()}
                          </span>
                        </div>

                        <h3 className="font-extrabold text-sm text-midnight-950 mb-1">{org.name}</h3>
                        <p className="text-xs text-midnight-500 mb-4">{org.industry || "Software & Technology"}</p>
                      </div>

                      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-midnight-100 text-center">
                        <div>
                          <span className="text-[10px] text-midnight-400 block">Members</span>
                          <span className="text-xs font-extrabold text-midnight-900">{org.user_count}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-midnight-400 block">Submissions</span>
                          <span className="text-xs font-extrabold text-midnight-900">{org.submission_count}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-midnight-400 block">Guidelines</span>
                          <span className="text-xs font-extrabold text-midnight-900">{org.guidelines_count}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. SYSTEM MONITORING TAB */}
            {activeTab === "monitoring" && health && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-5 rounded-3xl bg-white border border-midnight-100 shadow-card">
                    <div className="flex items-center gap-2 mb-2 text-emerald-600">
                      <Database className="w-5 h-5" />
                      <h4 className="font-bold text-xs uppercase tracking-wider text-midnight-900">Database Engine</h4>
                    </div>
                    <p className="text-lg font-extrabold text-midnight-950">{health.database_type}</p>
                    <p className="text-xs text-midnight-500 mt-1">Status: Fully Operational</p>
                  </div>

                  <div className="p-5 rounded-3xl bg-white border border-midnight-100 shadow-card">
                    <div className="flex items-center gap-2 mb-2 text-brand-600">
                      <Server className="w-5 h-5" />
                      <h4 className="font-bold text-xs uppercase tracking-wider text-midnight-900">API Server</h4>
                    </div>
                    <p className="text-lg font-extrabold text-midnight-950">FastAPI v1.0.0</p>
                    <p className="text-xs text-midnight-500 mt-1">Environment: {health.environment}</p>
                  </div>

                  <div className="p-5 rounded-3xl bg-white border border-midnight-100 shadow-card">
                    <div className="flex items-center gap-2 mb-2 text-purple-600">
                      <Activity className="w-5 h-5" />
                      <h4 className="font-bold text-xs uppercase tracking-wider text-midnight-900">Logged Audits</h4>
                    </div>
                    <p className="text-lg font-extrabold text-midnight-950">{health.total_records.audit_logs}</p>
                    <p className="text-xs text-midnight-500 mt-1">Tamper-evident audit events</p>
                  </div>
                </div>

                {/* Audit Log Stream */}
                <div className="bg-white rounded-3xl border border-midnight-100 shadow-card overflow-hidden">
                  <div className="p-5 border-b border-midnight-100">
                    <h3 className="text-xs font-bold text-midnight-950 uppercase tracking-wider">
                      Immutable System Audit Log (Latest 25 Events)
                    </h3>
                  </div>
                  <div className="divide-y divide-midnight-100">
                    {activities.map((act) => (
                      <div key={act.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs hover:bg-lavender-50/30">
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-lavender-100 text-midnight-800 border border-midnight-200">
                            {act.action}
                          </span>
                          <div>
                            <span className="font-semibold text-midnight-950">{act.user_name || "System"} </span>
                            <span className="text-midnight-400">({act.user_email || "system"}) </span>
                            <span className="text-midnight-600">• Entity: {act.entity_type}</span>
                          </div>
                        </div>
                        <span className="text-[11px] font-mono text-midnight-400">
                          {new Date(act.created_at).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Modal: Create User */}
        {showCreateUserModal && (
          <div className="fixed inset-0 z-50 bg-midnight-950/40 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-elevated border border-midnight-100">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-midnight-100">
                <h3 className="text-sm font-bold text-midnight-950 uppercase tracking-wider">Create New User</h3>
                <button onClick={() => setShowCreateUserModal(false)} className="text-midnight-400 hover:text-midnight-700">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateUser} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Full Name</label>
                  <input
                    type="text"
                    required
                    value={newUserName}
                    onChange={(e) => setNewUserName(e.target.value)}
                    placeholder="e.g. Jordan Lee"
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={newUserEmail}
                    onChange={(e) => setNewUserEmail(e.target.value)}
                    placeholder="jordan@company.com"
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={newUserPassword}
                    onChange={(e) => setNewUserPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Assigned Role</label>
                  <select
                    value={newUserRole}
                    onChange={(e) => setNewUserRole(e.target.value)}
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  >
                    <option value="creator">Creator (Drafts & fixes)</option>
                    <option value="reviewer">Reviewer (Approvals & governance)</option>
                    <option value="admin">Admin (Full administrative authority)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Organization Tenant</label>
                  <select
                    value={newUserOrgId}
                    onChange={(e) => setNewUserOrgId(e.target.value)}
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  >
                    <option value="">Select Organization...</option>
                    {orgsList.map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-midnight-100">
                  <button
                    type="button"
                    onClick={() => setShowCreateUserModal(false)}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold text-midnight-600 hover:bg-lavender-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creatingUser}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 disabled:opacity-50"
                  >
                    {creatingUser && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Create User</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Create Organization */}
        {showCreateOrgModal && (
          <div className="fixed inset-0 z-50 bg-midnight-950/40 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-elevated border border-midnight-100">
              <div className="flex items-center justify-between pb-3 mb-4 border-b border-midnight-100">
                <h3 className="text-sm font-bold text-midnight-950 uppercase tracking-wider">Create Organization</h3>
                <button onClick={() => setShowCreateOrgModal(false)} className="text-midnight-400 hover:text-midnight-700">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateOrg} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Organization Name</label>
                  <input
                    type="text"
                    required
                    value={newOrgName}
                    onChange={(e) => setNewOrgName(e.target.value)}
                    placeholder="e.g. Acme Health Technologies"
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-midnight-700 mb-1">Industry</label>
                  <input
                    type="text"
                    value={newOrgIndustry}
                    onChange={(e) => setNewOrgIndustry(e.target.value)}
                    placeholder="e.g. Healthcare Cloud SaaS"
                    className="w-full rounded-xl border border-midnight-200 p-2.5 text-xs focus:outline-none focus:border-brand-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-midnight-100">
                  <button
                    type="button"
                    onClick={() => setShowCreateOrgModal(false)}
                    className="px-3.5 py-2 rounded-xl text-xs font-semibold text-midnight-600 hover:bg-lavender-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={creatingOrg}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-midnight-900 hover:bg-midnight-800 disabled:opacity-50"
                  >
                    {creatingOrg && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                    <span>Create Organization</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
