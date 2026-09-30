
import { toast, type ToastPosition } from "react-toastify";
type ToastType = "success" | "error" | "warning" | "info";
export function showToast({ message, type = "info", duration = 2500, position = "top-right" as ToastPosition }: { message: string; type?: ToastType; duration?: number; position?: ToastPosition; }) {
  const options = { position, autoClose: duration, hideProgressBar: true, closeOnClick: true, theme: "dark" as const };
  switch (type) {
    case "success": return toast.success(message, options);
    case "error": return toast.error(message, options);
    case "warning": return toast.warning(message, options);
    default: return toast.info(message, options);
  }
}
