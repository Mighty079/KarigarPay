// api.js
// Configure your backend network settings here.
// IMPORTANT: If running the Expo app on a physical Android/iOS phone, replace "192.168.1.10"
// with your development machine's actual local IP address (e.g. 192.168.29.155) so that the phone
// can connect to the local FastAPI server over the same Wi-Fi network.

export const BACKEND_IP = "karigarpay-backend.onrender.com"; // CHANGE THIS to your machine's local IP (e.g. "192.168.x.x")
export const PORT = "";

const BASE_URL = `https://${BACKEND_IP}`;

export const api = {
  getWeaver: async () => {
    const res = await fetch(`${BASE_URL}/api/weaver`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  getWallet: async () => {
    const res = await fetch(`${BASE_URL}/api/wallet`);
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  buyYarn: async (amount) => {
    const res = await fetch(`${BASE_URL}/api/loan/buy-yarn`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  simulateSale: async (amount, description) => {
    const res = await fetch(`${BASE_URL}/api/simulate-sale`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount, description }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  toggleInsurance: async (enrolled) => {
    const res = await fetch(`${BASE_URL}/api/insurance/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enrolled }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  simulateMonth: async () => {
    const res = await fetch(`${BASE_URL}/api/insurance/simulate-month`, {
      method: "POST",
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  fileClaim: async (type) => {
    const res = await fetch(`${BASE_URL}/api/insurance/file-claim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type }),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  resetDatabase: async () => {
    const res = await fetch(`${BASE_URL}/api/reset`, {
      method: "POST",
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(parseError(errText));
    }
    return res.json();
  },
  
  baseUrl: BASE_URL,
};

// Helper function to extract FastAPI error detail
function parseError(errText) {
  try {
    const parsed = JSON.parse(errText);
    if (parsed.detail) {
      if (typeof parsed.detail === "string") return parsed.detail;
      if (Array.isArray(parsed.detail) && parsed.detail[0]?.msg) {
        return parsed.detail[0].msg;
      }
    }
    return errText;
  } catch (e) {
    return errText;
  }
}
