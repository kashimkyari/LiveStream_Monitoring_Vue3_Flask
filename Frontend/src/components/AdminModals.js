// AdminModals.js
import React, { useState } from 'react';
import axios from 'axios';

const modalStyles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundColor: 'rgba(0, 0, 0, 0.75)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1300,
    backdropFilter: 'blur(3px)',
  },
  modal: {
    width: '450px',
    backgroundColor: '#1a1a1a',
    borderRadius: '8px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
    border: '1px solid #2d2d2d',
    color: '#e0e0e0',
    fontFamily: "'Inter', sans-serif",
    animation: 'fadeIn 0.3s ease',
  },
  header: {
    padding: '16px 20px',
    borderBottom: '1px solid #2d2d2d',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: '1.2rem',
    fontWeight: '600',
  },
  closeButton: {
    background: 'transparent',
    border: 'none',
    color: '#999',
    fontSize: '1.2rem',
    cursor: 'pointer',
    padding: '5px',
    transition: 'color 0.2s',
  },
  body: {
    padding: '20px',
  },
  input: {
    width: '100%',
    padding: '12px',
    background: '#252525',
    border: '1px solid #444',
    borderRadius: '4px',
    color: '#e0e0e0',
    fontSize: '16px',
    marginBottom: '15px',
    transition: 'all 0.3s ease',
  },
  label: {
    display: 'block',
    marginBottom: '8px',
    fontWeight: '500',
  },
  footer: {
    padding: '16px 20px',
    borderTop: '1px solid #2d2d2d',
    display: 'flex',