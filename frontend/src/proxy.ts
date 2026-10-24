import { NextResponse, type NextRequest } from "next/server";

// Solo revisa que exista la cookie; quien valida la sesión de verdad es el backend (401 → login).
const COOKIE_SESION = "immpetus_sesion";

export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const tieneSesion = request.cookies.has(COOKIE_SESION);
  const esLogin = pathname === "/admin/login";

  if (!tieneSesion && !esLogin) {
    const url = new URL("/admin/login", request.url);
    url.searchParams.set("next", pathname + search);
    return NextResponse.redirect(url);
  }
  if (tieneSesion && esLogin) {
    return NextResponse.redirect(new URL("/admin", request.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/admin", "/admin/:path*"] };
