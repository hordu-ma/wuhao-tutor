/**
 * 学习问答 Pinia Store
 * 管理学习问答系统的状态，包括会话、消息、分析数据等
 */

import { defineStore } from "pinia";
import { ref, computed, reactive } from "vue";
import { ElMessage } from "element-plus";
import LearningAPI from "@/api/learning";
import type {
  ChatMessage,
  ChatState,
  ChatSession,
  AskQuestionRequest,
  CreateSessionRequest,
  UpdateSessionRequest,
  FeedbackRequest,
  SessionListQuery,
  LearningAnalytics,
  RecommendationResponse,
} from "@/types/learning";
import { SessionStatus } from "@/types/learning";

export const useLearningStore = defineStore("learning", () => {
  // ========== 状态定义 ==========

  // 聊天状态
  const chatState = reactive<ChatState>({
    messages: [],
    currentSession: undefined,
    sessions: [],
    isTyping: false,
    isLoading: false,
    error: undefined,
  });

  // 学习分析数据
  const analytics = ref<LearningAnalytics>();
  const recommendations = ref<RecommendationResponse>();

  // 加载状态
  const isLoadingAnalytics = ref(false);
  const isLoadingSessions = ref(false);
  const isLoadingRecommendations = ref(false);
  const isSubmittingQuestion = ref(false);

  // 分页状态
  const sessionPagination = reactive({
    total: 0,
    hasMore: false,
    nextOffset: 0,
    loading: false,
  });

  const questionPagination = reactive({
    total: 0,
    hasMore: false,
    nextOffset: 0,
    loading: false,
  });

  // ========== 计算属性 ==========

  const currentMessages = computed(() => chatState.messages);

  const activeSessions = computed(() =>
    chatState.sessions.filter(
      (session) => session.status === SessionStatus.ACTIVE
    )
  );

  const archivedSessions = computed(() =>
    chatState.sessions.filter(
      (session) => session.status === SessionStatus.ARCHIVED
    )
  );

  const hasCurrentSession = computed(() => !!chatState.currentSession);

  const canSendMessage = computed(
    () =>
      !isSubmittingQuestion.value && !chatState.isLoading && !chatState.isTyping
  );

  // 获取最新的活跃会话
  const latestActiveSession = computed(() => {
    const active = activeSessions.value;
    if (active.length === 0) return null;
    return active.reduce((latest, session) =>
      new Date(session.last_active_at || session.updated_at) >
      new Date(latest.last_active_at || latest.updated_at)
        ? session
        : latest
    );
  });

  // ========== Actions ==========

  /**
   * 初始化学习系统
   */
  async function initialize() {
    try {
      await Promise.all([
        loadSessions(),
        loadAnalytics(),
        loadRecommendations(),
      ]);
    } catch (error) {
      console.error("初始化学习系统失败:", error);
      ElMessage.error("初始化失败，请刷新页面重试");
    }
  }

  /**
   * 加载会话列表
   */
  async function loadSessions(query: SessionListQuery = {}) {
    if (isLoadingSessions.value) return;

    isLoadingSessions.value = true;
    try {
      const response = await LearningAPI.getSessionList({
        limit: 20,
        offset: 0,
        sort_by: "last_active_at",
        sort_order: "desc",
        ...query,
      });

      chatState.sessions = response.items;
      sessionPagination.total = response.total;
      sessionPagination.hasMore = response.has_more;
      sessionPagination.nextOffset = response.next_offset || 0;
    } catch (error) {
      console.error("加载会话列表失败:", error);
      ElMessage.error("加载会话列表失败");
      throw error;
    } finally {
      isLoadingSessions.value = false;
    }
  }

  /**
   * 加载更多会话
   */
  async function loadMoreSessions() {
    if (!sessionPagination.hasMore || sessionPagination.loading) return;

    sessionPagination.loading = true;
    try {
      const response = await LearningAPI.getSessionList({
        limit: 20,
        offset: sessionPagination.nextOffset,
        sort_by: "last_active_at",
        sort_order: "desc",
      });

      chatState.sessions.push(...response.items);
      sessionPagination.total = response.total;
      sessionPagination.hasMore = response.has_more;
      sessionPagination.nextOffset = response.next_offset || 0;
    } catch (error) {
      console.error("加载更多会话失败:", error);
      ElMessage.error("加载更多会话失败");
    } finally {
      sessionPagination.loading = false;
    }
  }

  /**
   * 创建新会话
   */
  async function createSession(
    request: CreateSessionRequest
  ): Promise<ChatSession> {
    try {
      const session = await LearningAPI.createSession(request);

      // 添加到会话列表开头
      chatState.sessions.unshift(session);

      return session;
    } catch (error) {
      console.error("创建会话失败:", error);
      ElMessage.error("创建会话失败");
      throw error;
    }
  }

  /**
   * 切换到指定会话
   */
  async function switchSession(sessionId: string) {
    if (chatState.currentSession?.id === sessionId) return;

    try {
      chatState.isLoading = true;

      // 获取会话详情
      const session = await LearningAPI.getSession(sessionId);

      // 加载会话的历史消息
      const history = await LearningAPI.getSessionQuestions(sessionId, 50, 0);

      // 转换为聊天消息格式
      const messages: ChatMessage[] = [];
      history.items.forEach((pair) => {
        // 添加用户问题
        messages.push({
          id: pair.question.id,
          type: "user",
          content: pair.question.content,
          timestamp: pair.question.created_at,
          question_id: pair.question.id,
          question_type: pair.question.question_type,
          subject: pair.question.subject,
          image_urls: pair.question.image_urls,
        });

        // 添加AI回答（如果有）
        if (pair.answer) {
          messages.push({
            id: pair.answer.id,
            type: "ai",
            content: pair.answer.content,
            timestamp: pair.answer.created_at,
            answer_id: pair.answer.id,
            question_id: pair.question.id,
          });
        }
      });

      // 按时间排序
      messages.sort(
        (a, b) =>
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      );

      // 更新状态
      chatState.currentSession = session;
      chatState.messages = messages;
      chatState.error = undefined;
    } catch (error) {
      console.error("切换会话失败:", error);
      ElMessage.error("切换会话失败");
      throw error;
    } finally {
      chatState.isLoading = false;
    }
  }

  /**
   * 发送问题
   */
  async function askQuestion(request: AskQuestionRequest) {
    if (!canSendMessage.value) return;

    isSubmittingQuestion.value = true;
    chatState.error = undefined;

    // 生成临时消息ID
    const tempQuestionId = `temp_${Date.now()}`;

    // 添加用户消息到界面
    const userMessage: ChatMessage = {
      id: tempQuestionId,
      type: "user",
      content: request.content,
      timestamp: new Date().toISOString(),
      question_type: request.question_type,
      subject: request.subject,
      image_urls: request.image_urls,
      is_processing: true,
    };
    chatState.messages.push(userMessage);

    // 添加AI思考中的占位符
    const thinkingMessage: ChatMessage = {
      id: `thinking_${Date.now()}`,
      type: "ai",
      content: "AI正在思考中...",
      timestamp: new Date().toISOString(),
      is_processing: true,
    };
    chatState.messages.push(thinkingMessage);
    chatState.isTyping = true;

    try {
      // 发送API请求
      const response = await LearningAPI.askQuestion({
        ...request,
        session_id: chatState.currentSession?.id,
      });

      // 移除思考中的占位符
      const thinkingIndex = chatState.messages.findIndex(
        (msg) => msg.id === thinkingMessage.id
      );
      if (thinkingIndex !== -1) {
        chatState.messages.splice(thinkingIndex, 1);
      }

      // 更新用户消息（移除处理中状态）
      const userIndex = chatState.messages.findIndex(
        (msg) => msg.id === tempQuestionId
      );
      if (userIndex !== -1) {
        chatState.messages[userIndex] = {
          ...chatState.messages[userIndex],
          id: response.question.id,
          question_id: response.question.id,
          is_processing: false,
        };
      }

      // 添加AI回答消息
      const aiMessage: ChatMessage = {
        id: response.answer.id,
        type: "ai",
        content: response.answer.content,
        timestamp: response.answer.created_at,
        answer_id: response.answer.id,
        question_id: response.question.id,
      };
      chatState.messages.push(aiMessage);

      // 更新会话信息
      if (response.session) {
        chatState.currentSession = response.session;

        // 更新会话列表中的会话
        const sessionIndex = chatState.sessions.findIndex(
          (s) => s.id === response.session.id
        );
        if (sessionIndex !== -1) {
          chatState.sessions[sessionIndex] = response.session;
        } else {
          // 新会话，添加到列表开头
          chatState.sessions.unshift(response.session);
        }
      }

      return response;
    } catch (error) {
      console.error("提问失败:", error);

      // 移除思考中的占位符
      const thinkingIndex = chatState.messages.findIndex(
        (msg) => msg.id === thinkingMessage.id
      );
      if (thinkingIndex !== -1) {
        chatState.messages.splice(thinkingIndex, 1);
      }

      // 更新用户消息显示错误状态
      const userIndex = chatState.messages.findIndex(
        (msg) => msg.id === tempQuestionId
      );
      if (userIndex !== -1) {
        chatState.messages[userIndex] = {
          ...chatState.messages[userIndex],
          is_processing: false,
          error: "发送失败",
        };
      }

      chatState.error = error instanceof Error ? error.message : "提问失败";
      ElMessage.error("提问失败，请重试");
      throw error;
    } finally {
      isSubmittingQuestion.value = false;
      chatState.isTyping = false;
    }
  }

  /**
   * 提交答案反馈
   */
  async function submitFeedback(request: FeedbackRequest) {
    try {
      await LearningAPI.submitFeedback(request);

      // 更新本地消息的反馈状态
      const message = chatState.messages.find(
        (msg) =>
          msg.answer_id === request.question_id ||
          msg.question_id === request.question_id
      );
      if (message && message.type === "ai") {
        // 这里可以添加反馈成功的视觉提示
        ElMessage.success("反馈已提交");
      }
    } catch (error) {
      console.error("提交反馈失败:", error);
      ElMessage.error("提交反馈失败");
      throw error;
    }
  }

  /**
   * 更新会话
   */
  async function updateSession(
    sessionId: string,
    request: UpdateSessionRequest
  ) {
    try {
      const updatedSession = await LearningAPI.updateSession(
        sessionId,
        request
      );

      // 更新当前会话
      if (chatState.currentSession?.id === sessionId) {
        chatState.currentSession = updatedSession;
      }

      // 更新会话列表
      const index = chatState.sessions.findIndex((s) => s.id === sessionId);
      if (index !== -1) {
        chatState.sessions[index] = updatedSession;
      }

      return updatedSession;
    } catch (error) {
      console.error("更新会话失败:", error);
      ElMessage.error("更新会话失败");
      throw error;
    }
  }

  /**
   * 删除会话
   */
  async function deleteSession(sessionId: string) {
    try {
      await LearningAPI.deleteSession(sessionId);

      // 从会话列表中移除
      const index = chatState.sessions.findIndex((s) => s.id === sessionId);
      if (index !== -1) {
        chatState.sessions.splice(index, 1);
      }

      // 如果删除的是当前会话，清空当前会话
      if (chatState.currentSession?.id === sessionId) {
        chatState.currentSession = undefined;
        chatState.messages = [];
      }

      ElMessage.success("会话已删除");
    } catch (error) {
      console.error("删除会话失败:", error);
      ElMessage.error("删除会话失败");
      throw error;
    }
  }

  /**
   * 归档会话
   */
  async function archiveSession(sessionId: string) {
    try {
      const updatedSession = await LearningAPI.archiveSession(sessionId);
      return await updateSession(sessionId, { status: updatedSession.status });
    } catch (error) {
      console.error("归档会话失败:", error);
      ElMessage.error("归档会话失败");
      throw error;
    }
  }

  /**
   * 激活会话
   */
  async function activateSession(sessionId: string) {
    try {
      const updatedSession = await LearningAPI.activateSession(sessionId);
      return await updateSession(sessionId, { status: updatedSession.status });
    } catch (error) {
      console.error("激活会话失败:", error);
      ElMessage.error("激活会话失败");
      throw error;
    }
  }

  /**
   * 加载学习分析数据
   */
  async function loadAnalytics() {
    if (isLoadingAnalytics.value) return;

    isLoadingAnalytics.value = true;
    try {
      analytics.value = await LearningAPI.getLearningAnalytics();
    } catch (error) {
      console.error("加载学习分析失败:", error);
      ElMessage.error("加载学习分析失败");
    } finally {
      isLoadingAnalytics.value = false;
    }
  }

  /**
   * 加载推荐内容
   */
  async function loadRecommendations() {
    if (isLoadingRecommendations.value) return;

    isLoadingRecommendations.value = true;
    try {
      recommendations.value = await LearningAPI.getRecommendations();
    } catch (error) {
      console.error("加载推荐内容失败:", error);
      ElMessage.error("加载推荐内容失败");
    } finally {
      isLoadingRecommendations.value = false;
    }
  }

  /**
   * 清空所有消息
   */
  function clearMessages() {
    chatState.messages = [];
  }

  /**
   * 清空当前会话
   */
  function clearCurrentSession() {
    chatState.currentSession = undefined;
    chatState.messages = [];
    chatState.error = undefined;
  }

  /**
   * 清除错误信息
   */
  function clearError() {
    chatState.error = undefined;
  }

  /**
   * 重置所有状态
   */
  function resetAll() {
    chatState.messages = [];
    chatState.currentSession = undefined;
    chatState.sessions = [];
    chatState.isTyping = false;
    chatState.isLoading = false;
    chatState.error = undefined;

    analytics.value = undefined;
    recommendations.value = undefined;

    sessionPagination.total = 0;
    sessionPagination.hasMore = false;
    sessionPagination.nextOffset = 0;

    questionPagination.total = 0;
    questionPagination.hasMore = false;
    questionPagination.nextOffset = 0;
  }

  // ========== 返回 Store API ==========

  return {
    // 状态
    chatState: readonly(chatState),
    analytics: readonly(analytics),
    recommendations: readonly(recommendations),

    // 加载状态
    isLoadingAnalytics: readonly(isLoadingAnalytics),
    isLoadingSessions: readonly(isLoadingSessions),
    isLoadingRecommendations: readonly(isLoadingRecommendations),
    isSubmittingQuestion: readonly(isSubmittingQuestion),

    // 分页状态
    sessionPagination: readonly(sessionPagination),
    questionPagination: readonly(questionPagination),

    // 计算属性
    currentMessages,
    activeSessions,
    archivedSessions,
    hasCurrentSession,
    canSendMessage,
    latestActiveSession,

    // 方法
    initialize,
    loadSessions,
    loadMoreSessions,
    createSession,
    switchSession,
    askQuestion,
    submitFeedback,
    updateSession,
    deleteSession,
    archiveSession,
    activateSession,
    loadAnalytics,
    loadRecommendations,
    clearMessages,
    clearCurrentSession,
    clearError,
    resetAll,
  };
});

export type LearningStore = ReturnType<typeof useLearningStore>;
