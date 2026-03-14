const Login = () => {
  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:8000/accounts/google/login/";
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center">
      <div className="bg-white rounded-3xl shadow-sm border border-slate-100 p-10 flex flex-col items-center gap-6">
        <h1 className="text-2xl font-black text-slate-800">
          Duty<span className="text-blue-600">Planner</span>
        </h1>
        <p className="text-sm text-slate-400 font-bold">Sign in to continue</p>
        <button
          onClick={handleGoogleLogin}
          className="flex items-center gap-3 px-6 py-3 bg-slate-900 text-white rounded-2xl font-black text-sm hover:bg-black transition-all shadow-xl shadow-slate-200 cursor-pointer"
        >
          Sign in with Google
        </button>
      </div>
    </div>
  );
};

export default Login;