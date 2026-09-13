// Centralized API Service for PlantAI
// Uses VITE_API_URL loaded from environment, defaulting to http://127.0.0.1:8000

const isDev = import.meta.env.DEV;
export const API_BASE_URL = import.meta.env.VITE_API_URL || (isDev ? "http://127.0.0.1:8000" : "");


/**
 * Upload an image to identify the plant species.
 * Section 30: uploadPlant() / identifyPlant()
 */
export async function uploadPlant(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/upload-image`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok && !data.message) {
      throw new Error("Unable to connect to PlantAI identification service.");
    }
    return data;
  } catch (err) {
    console.error("Plant identification error:", err);
    throw new Error("Unable to connect to PlantAI backend. Please make sure the backend server is running.");
  }
}

export const identifyPlant = uploadPlant;

/**
 * Upload a seed image to identify the seed species.
 * Section 30: identifySeed()
 */
export async function identifySeed(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/seed-identify`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok && !data.message) {
      throw new Error("Unable to connect to PlantAI seed identification service.");
    }
    return data;
  } catch (err) {
    console.error("Seed identification error:", err);
    throw new Error("Unable to connect to PlantAI backend. Please make sure the backend server is running.");
  }
}

/**
 * Upload an image of an affected plant or leaf for disease diagnosis.
 * Section 30: checkPlantHealth()
 */
export async function checkPlantHealth(file) {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE_URL}/health-check`, {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok && !data.message) {
      throw new Error("Unable to connect to PlantAI health diagnosis service.");
    }
    return data;
  } catch (err) {
    console.error("Plant health error:", err);
    throw new Error("Unable to connect to PlantAI backend. Please make sure the backend server is running.");
  }
}

/**
 * Retrieve plant care guidance from the MySQL database.
 * Section 30: getPlantCare()
 */
export async function getPlantCare(plantName) {
  if (!plantName || !plantName.trim()) {
    return { success: false, status: "error", message: "Plant name is required." };
  }

  try {
    const response = await fetch(
      `${API_BASE_URL}/plant-care/${encodeURIComponent(plantName.trim())}`
    );

    const data = await response.json();
    return data;
  } catch (err) {
    console.error("Plant care fetch error:", err);
    throw new Error("Unable to connect to PlantAI plant care service.");
  }
}

/**
 * Ask the AI Plant Assistant a botanical care question.
 * Section 30: askAssistant()
 */
export async function askAssistant(question, plantName = "") {
  try {
    const response = await fetch(`${API_BASE_URL}/assistant`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question: question.trim(),
        plant_name: (plantName || "").trim(),
      }),
    });

    const data = await response.json();
    return data;
  } catch (err) {
    console.error("Assistant chat error:", err);
    throw new Error("Unable to reach the PlantAI assistant. Please make sure the backend is online.");
  }
}

/**
 * User Registration
 */
export async function registerUser(name, email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    return await response.json();
  } catch (err) {
    console.error("Registration error:", err);
    throw new Error("Unable to connect to the authentication server.");
  }
}

/**
 * User Login
 */
export async function loginUser(email, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    return await response.json();
  } catch (err) {
    console.error("Login error:", err);
    throw new Error("Unable to connect to the authentication server.");
  }
}

export default {
  uploadPlant,
  identifyPlant,
  getPlantCare,
  askAssistant,
  checkPlantHealth,
  identifySeed,
  registerUser,
  loginUser,
  API_BASE_URL,
};
