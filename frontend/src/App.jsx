import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";


import ProtectedRoute from "./components/ProtectedRoute";
import AdminRoute from "./components/AdminRoute";
import AppLayout from "./layouts/AppLayout";


import Home from "./pages/Home";
import Services from "./pages/Services";


import ForgotPassword from "./pages/auth/ForgotPassword";
import Login from "./pages/auth/Login";
import Register from "./pages/auth/Register";
import ResetPassword from "./pages/auth/ResetPassword";


import AIAssistant from "./pages/ai/AIAssistant";


import ProviderDashboard from "./pages/provider/ProviderDashboard";
import ProviderServices from "./pages/provider/ProviderServices";
import ProviderBookings from "./pages/provider/ProviderBookings";
import ProviderPublicProfile from "./pages/provider/ProviderPublicProfile";
import ProviderAvailability from "./pages/provider/ProviderAvailability";
import ProviderEarnings from "./pages/provider/ProviderEarnings";


import Addresses from "./pages/user/Addresses";
import BookingHistory from "./pages/user/BookingHistory";
import FavoriteProviders from "./pages/user/FavoriteProviders";
import Profile from "./pages/user/Profile";


import AdminLogin from "./pages/admin/AdminLogin";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ProviderApplications from "./pages/admin/ProviderApplications";
import ProviderDetails from "./pages/admin/ProviderDetails";
import AdminBookings from "./pages/admin/AdminBookings";
import AdminPayments from "./pages/admin/AdminPayments";


import Messages from "./pages/Messages";


import "./App.css";


function App() {
  return (
    <Routes>

      {/* =====================================================
          NORMAL WEBSITE LAYOUT
      ====================================================== */}

      <Route element={<AppLayout />}>

        {/* ===================================================
            PUBLIC ROUTES
        ==================================================== */}

        <Route
          path="/"
          element={<Home />}
        />

        <Route
          path="/services"
          element={<Services />}
        />

        <Route
          path="/providers/:providerId"
          element={<ProviderPublicProfile />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        <Route
          path="/forgot-password"
          element={<ForgotPassword />}
        />

        <Route
          path="/reset-password"
          element={<ResetPassword />}
        />


        {/* ===================================================
            AUTHENTICATED USER ROUTES
        ==================================================== */}

        <Route element={<ProtectedRoute />}>

          <Route
            path="/profile"
            element={<Profile />}
          />

          <Route
            path="/bookings"
            element={<BookingHistory />}
          />

          <Route
            path="/addresses"
            element={<Addresses />}
          />

          <Route
            path="/favorites"
            element={<FavoriteProviders />}
          />

          <Route
            path="/ai-assistant"
            element={<AIAssistant />}
          />

          <Route
            path="/messages"
            element={<Messages />}
          />

        </Route>


        {/* ===================================================
            PROVIDER-ONLY ROUTES
        ==================================================== */}

        <Route
          element={
            <ProtectedRoute
              allowedRoles={["provider"]}
            />
          }
        >

          <Route
            path="/provider"
            element={<ProviderDashboard />}
          />

          <Route
            path="/provider/services"
            element={<ProviderServices />}
          />

          <Route
            path="/provider/bookings"
            element={<ProviderBookings />}
          />

          <Route
            path="/provider/availability"
            element={<ProviderAvailability />}
          />

          <Route
            path="/provider/earnings"
            element={<ProviderEarnings />}
          />

        </Route>

      </Route>


      {/* =====================================================
          ADMIN LOGIN
      ====================================================== */}

      <Route
        path="/admin/login"
        element={<AdminLogin />}
      />


      {/* =====================================================
          ADMIN-ONLY ROUTES
      ====================================================== */}

      <Route element={<AdminRoute />}>

        <Route
          path="/admin"
          element={<AdminDashboard />}
        />

        <Route
          path="/admin/providers"
          element={<ProviderApplications />}
        />

        <Route
          path="/admin/providers/:providerId"
          element={<ProviderDetails />}
        />

        <Route
          path="/admin/bookings"
          element={<AdminBookings />}
        />

        <Route
          path="/admin/payments"
          element={<AdminPayments />}
        />

      </Route>


      {/* =====================================================
          UNKNOWN ROUTES
      ====================================================== */}

      <Route
        path="*"
        element={
          <Navigate
            to="/"
            replace
          />
        }
      />

    </Routes>
  );
}


export default App;