/**
 * 作业相关状态管理
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { homeworkAPI } from "@/api/homework";
import type {
  HomeworkRecord,
  HomeworkSubmitRequest,
  HomeworkQueryParams,
  HomeworkStatus,
} from "@/types/homework";

export const useHomeworkStore = defineStore("homework", () => {
  // ========== 状态 ==========

  // 作业列表
  const homeworkList = ref<HomeworkRecord[]>([]);

  // 当前作业详情
  const currentHomework = ref<HomeworkRecord | null>(null);

  // 列表加载状态
  const listLoading = ref(false);

  // 详情加载状态
  const detailLoading = ref(false);

  // 提交作业加载状态
  const submitLoading = ref(false);

  // 批改作业加载状态
  const correctLoading = ref(false);

  // 分页信息
  const pagination = ref({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 0,
  });

  // 查询参数
  const queryParams = ref<HomeworkQueryParams>({
    page: 1,
    page_size: 20,
  });

  // 作业统计
  const stats = ref({
    total: 0,
    completed: 0,
    processing: 0,
    failed: 0,
    by_subject: {} as Record<string, number>,
    by_grade: {} as Record<string, number>,
  });

  // ========== 计算属性 ==========

  // 是否有作业数据
  const hasHomework = computed(() => homeworkList.value.length > 0);

  // 当前页作业数量
  const currentPageCount = computed(() => homeworkList.value.length);

  // 是否还有更多页
  const hasMorePages = computed(
    () => pagination.value.page < pagination.value.total_pages
  );

  // 按状态分组的作业
  const homeworkByStatus = computed(() => {
    const groups: Record<HomeworkStatus, HomeworkRecord[]> = {
      submitted: [],
      processing: [],
      completed: [],
      failed: [],
    };

    homeworkList.value.forEach((homework) => {
      groups[homework.status].push(homework);
    });

    return groups;
  });

  // ========== Actions ==========

  /**
   * 获取作业列表
   */
  const getHomeworkList = async (
    params?: HomeworkQueryParams,
    append = false
  ) => {
    try {
      listLoading.value = true;

      const searchParams = { ...queryParams.value, ...params };
      const response = await homeworkAPI.getHomeworkList(searchParams);

      if (append) {
        homeworkList.value.push(...response.items);
      } else {
        homeworkList.value = response.items;
      }

      // 更新分页信息
      pagination.value = {
        page: response.page,
        page_size: response.page_size,
        total: response.total,
        total_pages: response.total_pages,
      };

      // 更新查询参数
      Object.assign(queryParams.value, searchParams);
    } catch (error) {
      console.error("获取作业列表失败:", error);
      ElMessage.error("获取作业列表失败");
    } finally {
      listLoading.value = false;
    }
  };

  /**
   * 获取作业详情
   */
  const getHomeworkDetail = async (homeworkId: string) => {
    try {
      detailLoading.value = true;
      currentHomework.value = await homeworkAPI.getHomework(homeworkId);
    } catch (error) {
      console.error("获取作业详情失败:", error);
      ElMessage.error("获取作业详情失败");
    } finally {
      detailLoading.value = false;
    }
  };

  /**
   * 提交作业
   */
  const submitHomework = async (
    data: HomeworkSubmitRequest
  ): Promise<HomeworkRecord | null> => {
    try {
      submitLoading.value = true;
      const homework = await homeworkAPI.submitHomework(data);

      // 添加到列表首位
      homeworkList.value.unshift(homework);

      ElMessage.success("作业提交成功");
      return homework;
    } catch (error) {
      console.error("提交作业失败:", error);
      ElMessage.error("提交作业失败");
      return null;
    } finally {
      submitLoading.value = false;
    }
  };

  /**
   * 批改作业
   */
  const correctHomework = async (homeworkId: string) => {
    try {
      correctLoading.value = true;
      const result = await homeworkAPI.correctHomework(homeworkId);

      // 更新列表中的作业状态
      const homework = homeworkList.value.find((h) => h.id === homeworkId);
      if (homework) {
        homework.status = "completed" as HomeworkStatus;
        homework.correction_result = result;
        homework.updated_at = new Date().toISOString();
      }

      // 更新当前作业详情
      if (currentHomework.value?.id === homeworkId) {
        currentHomework.value.status = "completed" as HomeworkStatus;
        currentHomework.value.correction_result = result;
        currentHomework.value.updated_at = new Date().toISOString();
      }

      ElMessage.success("作业批改完成");
      return result;
    } catch (error) {
      console.error("批改作业失败:", error);
      ElMessage.error("批改作业失败");
      return null;
    } finally {
      correctLoading.value = false;
    }
  };

  /**
   * 删除作业
   */
  const deleteHomework = async (homeworkId: string) => {
    try {
      await homeworkAPI.deleteHomework(homeworkId);

      // 从列表中移除
      const index = homeworkList.value.findIndex((h) => h.id === homeworkId);
      if (index !== -1) {
        homeworkList.value.splice(index, 1);
        pagination.value.total--;
      }

      // 清空当前详情
      if (currentHomework.value?.id === homeworkId) {
        currentHomework.value = null;
      }

      ElMessage.success("作业删除成功");
    } catch (error) {
      console.error("删除作业失败:", error);
      ElMessage.error("删除作业失败");
    }
  };

  /**
   * 批量删除作业
   */
  const batchDeleteHomework = async (homeworkIds: string[]) => {
    try {
      await homeworkAPI.batchDeleteHomework(homeworkIds);

      // 从列表中移除
      homeworkList.value = homeworkList.value.filter(
        (h) => !homeworkIds.includes(h.id)
      );
      pagination.value.total -= homeworkIds.length;

      ElMessage.success(`成功删除 ${homeworkIds.length} 个作业`);
    } catch (error) {
      console.error("批量删除作业失败:", error);
      ElMessage.error("批量删除作业失败");
    }
  };

  /**
   * 获取作业统计
   */
  const getHomeworkStats = async () => {
    try {
      stats.value = await homeworkAPI.getHomeworkStats();
    } catch (error) {
      console.error("获取作业统计失败:", error);
    }
  };

  /**
   * 重新批改作业
   */
  const retryCorrection = async (homeworkId: string) => {
    try {
      const result = await homeworkAPI.retryCorrection(homeworkId);

      // 更新作业状态
      const homework = homeworkList.value.find((h) => h.id === homeworkId);
      if (homework) {
        homework.status = "completed" as HomeworkStatus;
        homework.correction_result = result;
        homework.updated_at = new Date().toISOString();
      }

      if (currentHomework.value?.id === homeworkId) {
        currentHomework.value.status = "completed" as HomeworkStatus;
        currentHomework.value.correction_result = result;
        currentHomework.value.updated_at = new Date().toISOString();
      }

      ElMessage.success("重新批改完成");
      return result;
    } catch (error) {
      console.error("重新批改失败:", error);
      ElMessage.error("重新批改失败");
      return null;
    }
  };

  /**
   * 更新作业信息
   */
  const updateHomework = async (
    homeworkId: string,
    data: Partial<Pick<HomeworkRecord, "title" | "description">>
  ) => {
    try {
      const updatedHomework = await homeworkAPI.updateHomework(
        homeworkId,
        data
      );

      // 更新列表中的作业
      const index = homeworkList.value.findIndex((h) => h.id === homeworkId);
      if (index !== -1) {
        homeworkList.value[index] = updatedHomework;
      }

      // 更新当前作业详情
      if (currentHomework.value?.id === homeworkId) {
        currentHomework.value = updatedHomework;
      }

      return updatedHomework;
    } catch (error) {
      console.error("更新作业失败:", error);
      ElMessage.error("更新作业失败");
      throw error;
    }
  };

  /**
   * 更新查询参数
   */
  const updateQueryParams = (params: Partial<HomeworkQueryParams>) => {
    Object.assign(queryParams.value, params);
  };

  /**
   * 重置查询参数
   */
  const resetQueryParams = () => {
    queryParams.value = {
      page: 1,
      page_size: 20,
    };
  };

  /**
   * 清空作业列表
   */
  const clearHomeworkList = () => {
    homeworkList.value = [];
    pagination.value = {
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    };
  };

  /**
   * 设置当前作业
   */
  const setCurrentHomework = (homework: HomeworkRecord | null) => {
    currentHomework.value = homework;
  };

  return {
    // 状态
    homeworkList,
    currentHomework,
    listLoading,
    detailLoading,
    submitLoading,
    correctLoading,
    pagination,
    queryParams,
    stats,

    // 计算属性
    hasHomework,
    currentPageCount,
    hasMorePages,
    homeworkByStatus,

    // Actions
    getHomeworkList,
    getHomeworkDetail,
    submitHomework,
    correctHomework,
    deleteHomework,
    batchDeleteHomework,
    getHomeworkStats,
    retryCorrection,
    updateHomework,
    updateQueryParams,
    resetQueryParams,
    clearHomeworkList,
    setCurrentHomework,
  };
});
