import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import axios from "axios";
import { io } from "socket.io-client";

export function useMessageData(user) {
  const messages = ref([]);
  const isLoading = ref(false);
  const error = ref(null);
  const socket = ref(null);
  const isConnected = ref(false);
  const onlineUsers = ref({});
  const typingUsers = ref({});

  // Calculate unread message count
  const messageUnreadCount = computed(() => {
    if (!messages.value) return 0;
    return messages.value.filter(
      (msg) => !msg.read && msg.receiver_id === user.value?.id
    ).length;
  });

  // Fetch all messages for the current user
  const fetchMessages = async () => {
    if (!user.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await axios.get("/api/messages");
      messages.value = response.data;
    } catch (err) {
      console.error("Error fetching messages:", err);
      error.value = err.message || "Failed to fetch messages";
    } finally {
      isLoading.value = false;
    }
  };

  // Fetch messages with a specific user
  const fetchConversation = async (userId) => {
    if (!user.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await axios.get(`/api/messages/${userId}`);
      return response.data;
    } catch (err) {
      console.error("Error fetching conversation:", err);
      error.value = err.message || "Failed to fetch conversation";
      return [];
    } finally {
      isLoading.value = false;
    }
  };

  // Mark a message as read
  const markAsRead = async (messageId) => {
    try {
      await axios.put(`/api/messages/${messageId}/mark-read`);
      // Update the local state
      const messageIndex = messages.value.findIndex((m) => m.id === messageId);
      if (messageIndex !== -1) {
        messages.value[messageIndex].read = true;
      }
    } catch (err) {
      console.error("Error marking message as read:", err);
    }
  };

  // Send a new message
  const sendMessage = async (receiverId, content, attachment = null) => {
    const messageData = {
      receiver_id: receiverId,
      message: content,
    };

    if (attachment) {
      messageData.attachment_id = attachment.id;
    }

    try {
      const response = await axios.post("/api/messages", messageData);

      // Emit via socket if connected
      if (isConnected.value && socket.value) {
        const receiver = await getUserById(receiverId);
        if (receiver) {
          socket.value.emit("send_message", {
            receiver_username: receiver.username,
            message: content,
            attachment: attachment,
          });
        }
      }

      // Add the new message to our local state
      messages.value.push(response.data);
      return response.data;
    } catch (err) {
      console.error("Error sending message:", err);
      throw err;
    }
  };

  // Upload a file attachment
  const uploadAttachment = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("/api/attachments/upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    } catch (err) {
      console.error("Error uploading attachment:", err);
      throw err;
    }
  };

  // Send typing indicator
  const sendTypingIndicator = (receiverId, isTyping) => {
    if (!isConnected.value || !socket.value) return;

    getUserById(receiverId).then((receiver) => {
      if (receiver) {
        socket.value.emit("typing", {
          receiver_username: receiver.username,
          typing: isTyping,
        });
      }
    });
  };

  // Helper to get user by ID
  const getUserById = async (userId) => {
    try {
      const response = await axios.get(`/api/users/${userId}`);
      return response.data;
    } catch (err) {
      console.error("Error fetching user:", err);
      return null;
    }
  };

  // Initialize socket connection
  const initSocket = () => {
    socket.value = io("     https://monitor-backend.jetcamstudio.com:5000messages", {
      path: "/ws",
      transports: ["websocket"],
    });

    socket.value.on("connect", () => {
      console.log("Socket connected");
      isConnected.value = true;
    });

    socket.value.on("disconnect", () => {
      console.log("Socket disconnected");
      isConnected.value = false;
    });

    socket.value.on("receive_message", (message) => {
      console.log("Received message:", message);

      // Update messages array if this message is not already in the list
      const existingIndex = messages.value.findIndex(
        (m) => m.id === message.id
      );
      if (existingIndex === -1) {
        messages.value.push(message);
      } else {
        // Update existing message
        messages.value[existingIndex] = message;
      }
    });

    socket.value.on("user_status", (data) => {
      console.log("User status update:", data);
      onlineUsers.value[data.userId] = data.online;
    });

    socket.value.on("initial_status", (data) => {
      console.log("Initial status:", data);
      data.users.forEach((user) => {
        onlineUsers.value[user.userId] = user.online;
      });
    });

    socket.value.on("typing", (data) => {
      console.log("Typing indicator:", data);
      typingUsers.value[data.sender_username] = data.typing;
    });

    socket.value.on("error", (data) => {
      console.error("Socket error:", data);
      error.value = data.error;
    });
  };

  // Clean up
  const cleanup = () => {
    if (socket.value) {
      socket.value.disconnect();
      socket.value = null;
    }
  };

  // Lifecycle hooks
  onMounted(() => {
    if (user.value) {
      fetchMessages();
      initSocket();
    }
  });

  onUnmounted(() => {
    cleanup();
  });

  // Watch for user changes and refresh messages
  watch(
    () => user.value,
    (newUser) => {
      if (newUser) {
        fetchMessages();

        if (!socket.value) {
          initSocket();
        }
      } else {
        cleanup();
      }
    }
  );

  return {
    messages,
    isLoading,
    error,
    messageUnreadCount,
    onlineUsers,
    typingUsers,
    isConnected,
    fetchMessages,
    fetchConversation,
    markAsRead,
    sendMessage,
    uploadAttachment,
    sendTypingIndicator,
  };
}
