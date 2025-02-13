import axios from 'axios';

const API_URL = "http://localhost:8000";

export const getTournaments = async () => {
  try {
    const response = await axios.get(`${API_URL}/tournament`);
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
