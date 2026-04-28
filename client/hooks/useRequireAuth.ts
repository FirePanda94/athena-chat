import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

export function useRequireAuth() {
  const { accessToken, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && accessToken === null) {
      router.push("/auth/login");
    }
  }, [accessToken, isLoading, router]);

  return { accessToken, isLoading };
}
