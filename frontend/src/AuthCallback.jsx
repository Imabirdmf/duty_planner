import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

const AuthCallback = ({ onAuth }) => {
  const navigate = useNavigate();

  useEffect(() => {
    const search = window.location.href.split('?')[1]?.split('#')[0];
    const params = new URLSearchParams(search);

    const access = params.get("access");
    const refresh = params.get("refresh");

    if (access && refresh) {
      onAuth(access, refresh);
      navigate("/", { replace: true });
    } else {
      navigate("/login", { replace: true });
    }
  }, []);

  return <div>Authorizing...</div>;
};

export default AuthCallback;