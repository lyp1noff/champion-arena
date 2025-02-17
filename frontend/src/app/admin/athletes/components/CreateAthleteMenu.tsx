"use client";

import React, { useState } from 'react';

const CreateAthleteMenu: React.FC = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [gender, setGender] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [coach, setCoach] = useState('');

  const handleSubmit = () => {
    const participantData = {
      firstName,
      lastName,
      gender,
      dateOfBirth,
      coach,
    };
    console.log('Participant Data:', participantData);
  };

  return (
    <div className="p-4 max-w-md mx-auto border rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">Add New Participant</h2>

      <div className="mb-4">
        <label htmlFor="firstName" className="block font-medium">First Name</label>
        <input
          id="firstName"
          className="w-full border p-2 rounded"
          value={firstName}
          onChange={(e) => setFirstName(e.target.value)}
          placeholder="Enter First Name"
        />
      </div>

      <div className="mb-4">
        <label htmlFor="lastName" className="block font-medium">Last Name</label>
        <input
          id="lastName"
          className="w-full border p-2 rounded"
          value={lastName}
          onChange={(e) => setLastName(e.target.value)}
          placeholder="Enter Last Name"
        />
      </div>

      <div className="mb-4">
        <label htmlFor="gender" className="block font-medium">Gender</label>
        <select
          id="gender"
          className="w-full border p-2 rounded"
          value={gender}
          onChange={(e) => setGender(e.target.value)}
        >
          <option value="">Select Gender</option>
          <option value="Male">Male</option>
          <option value="Female">Female</option>
        </select>
      </div>

      <div className="mb-4">
        <label htmlFor="dateOfBirth" className="block font-medium">Date of Birth</label>
        <input
          id="dateOfBirth"
          type="date"
          className="w-full border p-2 rounded"
          value={dateOfBirth}
          onChange={(e) => setDateOfBirth(e.target.value)}
        />
      </div>

      <div className="mb-4">
        <label htmlFor="coach" className="block font-medium">Coach</label>
        <input
          id="coach"
          className="w-full border p-2 rounded"
          value={coach}
          onChange={(e) => setCoach(e.target.value)}
          placeholder="Enter Coach's Name"
        />
      </div>

      <button
        className="w-full bg-blue-500 text-white p-2 rounded mt-4 hover:bg-blue-600"
        onClick={handleSubmit}
      >
        Add Participant
      </button>
    </div>
  );
};

export default CreateAthleteMenu;
