<Route element={<AdminRoute />}>
  <Route element={<AdminLayout />}>
    <Route path="/admin" element={<AdminDashboard />} />
    <Route
      path="/admin/providers"
      element={<ProviderApplications />}
    />
    <Route
      path="/admin/providers/:providerId"
      element={<ProviderDetails />}
    />
  </Route>
</Route>