import axios from 'axios';

const API_URL = "http://localhost:8000";

export const getTournaments = async () => {
  try {
    const response = await axios.get(`${API_URL}/tournaments`);
    return response.data;
  } catch (error) {
    console.error("Error fetching tournaments:", error);
    return [];
  }
};

export const getTournament = async (id: number) => {
  try {
    const response = await axios.get(`${API_URL}/tournament/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching tournaments:", error);
    return [];
  }
};

export const createTournament = async (data: { name: string, location: string, date: string }) => {
  try {
    const response = await axios.post(`${API_URL}/tournaments`, data);
    return response.data;
  } catch (error) {
    console.error("Error creating tournament:", error);
  }
};

export const getAthletes = async () => {
  try {
    const response = await axios.get(`${API_URL}/athletes`);
    return response.data;
  } catch (error) {
    console.error("Error fetching athletes:", error);
    return [];
  }
};

export const getAthlete = async (id: number) => {
  try {
    const response = await axios.get(`${API_URL}/athlete/${id}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching athletes:", error);
    return [];
  }
};

export const createAthlete = async (data: { name: string, location: string, date: string }) => {
  try {
    const response = await axios.post(`${API_URL}/athletes`, data);
    return response.data;
  } catch (error) {
    console.error("Error creating athlete:", error);
  }
};
