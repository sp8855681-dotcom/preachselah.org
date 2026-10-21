const signInTab = document.getElementById("sign-in-tab");
const createAccountTab = document.getElementById("create-account-tab");
const authForm = document.getElementById("auth-form");
const passwordInput = document.getElementById("auth-password");
let creatingAccount = new URLSearchParams(window.location.search).get("mode") === "register";

const appSplash = document.getElementById("app-splash");
const splashDelay = window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 150 : 1100;
if (appSplash) {
  window.setTimeout(() => {
    if (!appSplash.isConnected) return;
    appSplash.classList.add("app-splash-hidden");
    appSplash.addEventListener("transitionend", () => appSplash.remove(), { once: true });
    window.setTimeout(() => appSplash.remove(), 700);
  }, splashDelay);
}

function setAuthMode(createAccount) {
  creatingAccount = createAccount;
  authForm.action = createAccount ? "/register" : "/login";
  document.getElementById("auth-heading").textContent = createAccount ? "A fresh beginning." : "Welcome back.";
  document.getElementById("auth-subheading").textContent = createAccount
    ? "Create an account to make this space yours."
    : "Sign in with your email to continue.";
  document.getElementById("auth-submit").innerHTML = createAccount
    ? 'Create my account <span>↗</span>'
    : 'Sign in <span>↗</span>';
  signInTab.classList.toggle("active", !createAccount);
  createAccountTab.classList.toggle("active", createAccount);
  signInTab.setAttribute("aria-selected", String(!createAccount));
  createAccountTab.setAttribute("aria-selected", String(createAccount));
  passwordInput.autocomplete = createAccount ? "new-password" : "current-password";
  document.getElementById("auth-name-note").hidden = !createAccount;
}

signInTab.addEventListener("click", () => setAuthMode(false));
createAccountTab.addEventListener("click", () => setAuthMode(true));
setAuthMode(creatingAccount);
