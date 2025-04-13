<template>
  <div :style="styles.container">
    <!-- Keywords Section -->
    <div :style="styles.section">
      <div :style="styles.sectionHeader">Chat Keywords</div>
      <input
        type="text"
        :style="styles.input"
        placeholder="Enter new keyword"
        v-model="newKeyword"
      />
      <button :style="styles.button" @click="handleAddKeyword">
        Add Keyword
      </button>
      <div :style="styles.tableContainer">
        <table :style="styles.table">
          <thead>
            <tr>
              <th :style="styles.th">ID</th>
              <th :style="styles.th">Keyword</th>
              <th :style="styles.th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="chatKeywords.length === 0">
              <td colspan="3" style="text-align: center; padding: 1rem">
                No keywords found.
              </td>
            </tr>
            <tr v-for="kw in chatKeywords" :key="kw.id">
              <td :style="styles.td">{{ kw.id }}</td>
              <td :style="styles.td">{{ kw.keyword }}</td>
              <td :style="styles.td">
                <button :style="styles.btnSecondary" @click="handleEditKeyword(kw.id, kw.keyword)">
                  Edit
                </button>
                <button :style="styles.btnDanger" @click="handleDeleteKeyword(kw.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Flagged Objects Section -->
    <div :style="styles.section">
      <div :style="styles.sectionHeader">Flagged Objects</div>
      <input
        type="text"
        :style="styles.input"
        placeholder="Enter new object name"
        v-model="newObject"
      />
      <button :style="styles.button" @click="handleAddObject">
        Add Object
      </button>
      <div :style="styles.tableContainer">
        <table :style="styles.table">
          <thead>
            <tr>
              <th :style="styles.th">ID</th>
              <th :style="styles.th">Object Name</th>
              <th :style="styles.th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="flaggedObjects.length === 0">
              <td colspan="3" style="text-align: center; padding: 1rem">
                No flagged objects found.
              </td>
            </tr>
            <tr v-for="obj in flaggedObjects" :key="obj.id">
              <td :style="styles.td">{{ obj.id }}</td>
              <td :style="styles.td">{{ obj.object_name }}</td>
              <td :style="styles.td">
                <button :style="styles.btnSecondary" @click="handleEditObject(obj.id, obj.object_name)">
                  Edit
                </button>
                <button :style="styles.btnDanger" @click="handleDeleteObject(obj.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Telegram Recipients Section -->
    <div :style="styles.section">
      <div :style="styles.sectionHeader">Telegram Recipients</div>
      <input
        type="text"
        :style="styles.input"
        placeholder="Enter Telegram username"
        v-model="newTelegramUsername"
      />
      <input
        type="text"
        :style="styles.input"
        placeholder="Enter Chat ID"
        v-model="newTelegramChatId"
      />
      <button :style="styles.button" @click="handleAddRecipient">
        Add Recipient
      </button>
      <div :style="styles.tableContainer">
        <table :style="styles.table">
          <thead>
            <tr>
              <th :style="styles.th">Username</th>
              <th :style="styles.th">Chat ID</th>
              <th :style="styles.th">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="telegramRecipients.length === 0">
              <td colspan="3" style="text-align: center; padding: 1rem">
                No recipients found.
              </td>
            </tr>
            <tr v-for="recipient in telegramRecipients" :key="recipient.id">
              <td :style="styles.td">{{ recipient.telegram_username }}</td>
              <td :style="styles.td">{{ recipient.chat_id }}</td>
              <td :style="styles.td">
                <button :style="styles.btnDanger" @click="handleDeleteRecipient(recipient.id)">
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import axios from 'axios';

export default {
  name: 'FlagSettingsPage',
  setup() {
    // Create a toast function that falls back to console.log if no toast service is available
    const showToast = (message, type) => {
      // In a real app, you'd integrate with your Vue toast system here
      console.log(`[${type}] ${message}`);
    };

    // Styles object (kept same as in React version)
    const styles = {
      container: {
        padding: '16px',
        maxWidth: '1200px',
        margin: '0 auto',
        animation: 'slideUp 0.6s cubic-bezier(0.22, 1, 0.36, 1)',
        color: '#e0e0e0',
        fontFamily: "'Inter', sans-serif",
      },
      title: {
        fontSize: '1.8rem',
        fontWeight: 'bold',
        marginBottom: '1.5rem',
        textAlign: 'center',
      },
      section: {
        margin: '1.5rem 0',
        padding: '1rem',
        background: '#1a1a1a',
        borderRadius: '8px',
        border: '1px solid #2d2d2d',
      },
      sectionHeader: {
        marginBottom: '1rem',
        fontSize: '1.5rem',
        fontWeight: 'bold',
        color: '#e0e0e0',
      },
      input: {
        width: '100%',
        padding: '0.75rem',
        background: '#252525',
        border: '1px solid #444',
        borderRadius: '4px',
        color: '#e0e0e0',
        fontSize: '16px',
        transition: 'all 0.3s ease',
        marginBottom: '1rem',
      },
      button: {
        padding: '0.75rem 1.25rem',
        background: 'linear-gradient(135deg, #007bff, #0056b3)',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        fontWeight: '500',
        transition: 'all 0.3s ease',
        marginBottom: '1rem',
      },
      tableContainer: {
        overflowX: 'auto',
      },
      table: {
        width: '100%',
        borderCollapse: 'collapse',
        background: '#1a1a1a',
        borderRadius: '8px',
        overflow: 'hidden',
      },
      th: {
        padding: '0.75rem 1rem',
        textAlign: 'left',
        background: '#252525',
        color: '#e0e0e0',
        fontWeight: '500',
        borderBottom: '1px solid #444',
        whiteSpace: 'nowrap',
      },
      td: {
        padding: '0.75rem 1rem',
        borderBottom: '1px solid #2d2d2d',
        color: '#e0e0e0',
      },
      btnSecondary: {
        padding: '0.5rem 0.75rem',
        background: '#6c757d',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
        marginRight: '0.5rem',
      },
      btnDanger: {
        padding: '0.5rem 0.75rem',
        background: '#ff4444',
        color: 'white',
        border: 'none',
        borderRadius: '4px',
        cursor: 'pointer',
      },
    };

    // ---------------------------
    // Keywords Section
    // ---------------------------
    const chatKeywords = ref([]);
    const newKeyword = ref('');

    const fetchKeywords = async () => {
      try {
        const res = await axios.get('/api/keywords');
        chatKeywords.value = res.data;
      } catch (error) {
        console.error('Error fetching keywords:', error);
        showToast('Error fetching keywords', 'error');
      }
    };

    const handleAddKeyword = async () => {
      if (!newKeyword.value.trim()) {
        showToast('Keyword is required.', 'error');
        return;
      }
      try {
        const res = await axios.post('/api/keywords', { keyword: newKeyword.value.trim() });
        showToast(res.data.message || 'Keyword added successfully', 'success');
        newKeyword.value = '';
        fetchKeywords();
      } catch (error) {
        const msg = error.response?.data.message || '';
        if (error.response && error.response.status === 400 && (msg.toLowerCase().includes('exists') || msg.toLowerCase().includes('already'))) {
          showToast('Keyword already exists', 'info');
          newKeyword.value = '';
          fetchKeywords();
        } else {
          showToast(msg || 'Error adding keyword.', 'error');
        }
      }
    };

    const handleEditKeyword = async (id, currentKeyword) => {
      const updated = prompt('Enter new keyword:', currentKeyword);
      if (updated && updated.trim() !== currentKeyword) {
        try {
          await axios.put(`/api/keywords/${id}`, { keyword: updated.trim() });
          showToast('Keyword updated successfully', 'success');
          fetchKeywords();
        } catch (error) {
          showToast(error.response?.data.message || 'Error updating keyword.', 'error');
          console.error('Error updating keyword:', error);
        }
      }
    };

    const handleDeleteKeyword = async (id) => {
      try {
        await axios.delete(`/api/keywords/${id}`);
        showToast('Keyword deleted successfully', 'success');
        fetchKeywords();
      } catch (error) {
        const msg = error.response?.data.message || '';
        if (error.response && error.response.status === 400 && (msg.toLowerCase().includes('deleted') || msg.toLowerCase().includes('not found'))) {
          showToast('Keyword deleted successfully', 'info');
          fetchKeywords();
        } else {
          showToast('Error deleting keyword.', 'error');
          console.error('Error deleting keyword:', error);
        }
      }
    };

    // ---------------------------
    // Flagged Objects Section
    // ---------------------------
    const flaggedObjects = ref([]);
    const newObject = ref('');

    const fetchObjects = async () => {
      try {
        const res = await axios.get('/api/objects');
        flaggedObjects.value = res.data;
      } catch (error) {
        console.error('Error fetching objects:', error);
        showToast('Error fetching flagged objects', 'error');
      }
    };

    const handleAddObject = async () => {
      if (!newObject.value.trim()) {
        showToast('Object name is required.', 'error');
        return;
      }
      try {
        const res = await axios.post('/api/objects', { object_name: newObject.value.trim() });
        showToast(res.data.message || 'Object added successfully', 'success');
        newObject.value = '';
        fetchObjects();
      } catch (error) {
        const msg = error.response?.data.message || '';
        if (error.response && error.response.status === 400 && (msg.toLowerCase().includes('exists') || msg.toLowerCase().includes('already'))) {
          showToast('Object already exists', 'info');
          newObject.value = '';
          fetchObjects();
        } else {
          showToast(msg || 'Error adding object.', 'error');
        }
      }
    };

    const handleEditObject = async (id, currentName) => {
      const updated = prompt('Enter new object name:', currentName);
      if (updated && updated.trim() !== currentName) {
        try {
          await axios.put(`/api/objects/${id}`, { object_name: updated.trim() });
          showToast('Object updated successfully', 'success');
          fetchObjects();
        } catch (error) {
          showToast(error.response?.data.message || 'Error updating object.', 'error');
          console.error('Error updating object:', error);
        }
      }
    };

    const handleDeleteObject = async (id) => {
      try {
        await axios.delete(`/api/objects/${id}`);
        showToast('Object deleted successfully', 'success');
        fetchObjects();
      } catch (error) {
        const msg = error.response?.data.message || '';
        if (error.response && error.response.status === 400 && (msg.toLowerCase().includes('deleted') || msg.toLowerCase().includes('not found'))) {
          showToast('Object deleted successfully', 'info');
          fetchObjects();
        } else {
          showToast('Error deleting object.', 'error');
          console.error('Error deleting object:', error);
        }
      }
    };

    // ---------------------------
    // Telegram Recipients Section
    // ---------------------------
    const telegramRecipients = ref([]);
    const newTelegramUsername = ref('');
    const newTelegramChatId = ref('');

    const fetchTelegramRecipients = async () => {
      try {
        const res = await axios.get('/api/telegram_recipients');
        telegramRecipients.value = res.data;
      } catch (error) {
        console.error('Error fetching Telegram recipients:', error);
        showToast('Error fetching Telegram recipients', 'error');
      }
    };

    const handleAddRecipient = async () => {
      if (!newTelegramUsername.value.trim() || !newTelegramChatId.value.trim()) {
        showToast('Both Telegram username and chat ID are required.', 'error');
        return;
      }
      try {
        const res = await axios.post('/api/telegram_recipients', {
          telegram_username: newTelegramUsername.value.trim(),
          chat_id: newTelegramChatId.value.trim(),
        });
        showToast(res.data.message || 'Recipient added successfully', 'success');
        newTelegramUsername.value = '';
        newTelegramChatId.value = '';
        fetchTelegramRecipients();
      } catch (error) {
        const msg = error.response?.data.message || '';
        if (error.response && error.response.status === 400 && (msg.toLowerCase().includes('exists') || msg.toLowerCase().includes('already'))) {
          showToast('Recipient already exists', 'info');
          newTelegramUsername.value = '';
          newTelegramChatId.value = '';
          fetchTelegramRecipients();
        } else {
          showToast(msg || 'Error adding recipient.', 'error');
        }
      }
    };

    const handleDeleteRecipient = async (id) => {
      try {
        await axios.delete(`/api/telegram_recipients/${id}`);
        showToast('Recipient deleted successfully', 'success');
        fetchTelegramRecipients();
      } catch (error) {
        const msg = error.response?.data.message || '';
        if (error.response && error.response.status === 400 && (msg.toLowerCase().includes('deleted') || msg.toLowerCase().includes('not found'))) {
          showToast('Recipient deleted successfully', 'info');
          fetchTelegramRecipients();
        } else {
          showToast('Error deleting recipient.', 'error');
          console.error('Error deleting recipient:', error);
        }
      }
    };

    // Fetch all data on component mount
    onMounted(() => {
      fetchKeywords();
      fetchObjects();
      fetchTelegramRecipients();
    });

    return {
      styles,
      // Keywords
      chatKeywords,
      newKeyword,
      handleAddKeyword,
      handleEditKeyword,
      handleDeleteKeyword,
      // Objects
      flaggedObjects,
      newObject,
      handleAddObject,
      handleEditObject,
      handleDeleteObject,
      // Telegram recipients
      telegramRecipients,
      newTelegramUsername,
      newTelegramChatId,
      handleAddRecipient,
      handleDeleteRecipient,
    };
  }
};
</script>