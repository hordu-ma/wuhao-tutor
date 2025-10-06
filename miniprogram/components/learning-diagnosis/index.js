Component({
  /**
   * 学情诊断报告组件
   * 基于个性化分析数据生成诊断报告
   */
  properties: {
    // 用户学习数据
    userData: {
      type: Object,
      value: {},
    },
    // 诊断数据
    diagnosisData: {
      type: Object,
      value: {},
    },
    // 是否显示详细信息
    showDetails: {
      type: Boolean,
      value: true,
    },
    // 报告类型
    reportType: {
      type: String,
      value: 'comprehensive', // comprehensive | simple | focus
    },
  },

  data: {
    // 诊断结果
    diagnosis: {
      overallScore: 0,
      level: '',
      levelColor: '',
      strengths: [],
      weaknesses: [],
      recommendations: [],
      improvementPlan: [],
    },
    
    // 学习风格分析
    learningStyle: {
      type: '',
      description: '',
      characteristics: [],
      suggestions: [],
    },

    // 知识点掌握情况
    knowledgeMastery: {
      totalPoints: 0,
      masteredPoints: 0,
      masteryRate: 0,
      weakPoints: [],
    },

    // 学习行为分析
    behaviorAnalysis: {
      studyFrequency: '',
      sessionDuration: 0,
      focusTime: '',
      preferredTime: '',
      activePatterns: [],
    },

    // 进步趋势
    progressTrend: {
      direction: '', // up | down | stable
      change: 0,
      timeframe: '',
      keyMetrics: [],
    },

    // 建议优先级
    priorities: [],
  },

  observers: {
    'userData, diagnosisData': function(userData, diagnosisData) {
      if (userData && Object.keys(userData).length > 0) {
        this.generateDiagnosis();
      }
    },
  },

  methods: {
    /**
     * 生成诊断报告
     */
    generateDiagnosis() {
      const { userData, diagnosisData } = this.properties;
      
      // 计算综合评分
      const overallScore = this.calculateOverallScore(userData);
      
      // 分析学习水平
      const level = this.analyzeLearningLevel(overallScore);
      
      // 识别优势和劣势
      const strengths = this.identifyStrengths(userData);
      const weaknesses = this.identifyWeaknesses(userData);
      
      // 生成建议
      const recommendations = this.generateRecommendations(userData, weaknesses);
      
      // 制定改进计划
      const improvementPlan = this.createImprovementPlan(weaknesses, recommendations);

      this.setData({
        diagnosis: {
          overallScore,
          level: level.name,
          levelColor: level.color,
          strengths,
          weaknesses,
          recommendations,
          improvementPlan,
        }
      });

      // 分析其他维度
      this.analyzeLearningStyle(userData);
      this.analyzeKnowledgeMastery(userData);
      this.analyzeBehaviorPatterns(userData);
      this.analyzeProgressTrend(userData);
      this.setPriorities();
    },

    /**
     * 计算综合评分
     */
    calculateOverallScore(userData) {
      const weights = {
        accuracy: 0.3,
        consistency: 0.2,
        participation: 0.2,
        improvement: 0.15,
        difficulty: 0.15,
      };

      let score = 0;
      score += (userData.accuracy || 0) * weights.accuracy;
      score += (userData.consistency || 0) * weights.consistency;
      score += (userData.participation || 0) * weights.participation;
      score += (userData.improvement || 0) * weights.improvement;
      score += (userData.difficulty || 0) * weights.difficulty;

      return Math.round(score * 100);
    },

    /**
     * 分析学习水平
     */
    analyzeLearningLevel(score) {
      if (score >= 90) {
        return { name: '优秀', color: '#52c41a' };
      } else if (score >= 80) {
        return { name: '良好', color: '#1890ff' };
      } else if (score >= 70) {
        return { name: '中等', color: '#faad14' };
      } else if (score >= 60) {
        return { name: '及格', color: '#fa8c16' };
      } else {
        return { name: '待提高', color: '#f5222d' };
      }
    },

    /**
     * 识别学习优势
     */
    identifyStrengths(userData) {
      const strengths = [];
      
      if (userData.accuracy > 0.8) {
        strengths.push({
          title: '解题准确率高',
          description: '在答题过程中表现出较高的准确性',
          score: userData.accuracy,
        });
      }

      if (userData.consistency > 0.7) {
        strengths.push({
          title: '学习习惯良好',
          description: '能够保持规律的学习节奏',
          score: userData.consistency,
        });
      }

      if (userData.participation > 0.8) {
        strengths.push({
          title: '学习积极性高',
          description: '主动参与学习活动，提问频率较高',
          score: userData.participation,
        });
      }

      return strengths;
    },

    /**
     * 识别薄弱环节
     */
    identifyWeaknesses(userData) {
      const weaknesses = [];

      if (userData.accuracy < 0.6) {
        weaknesses.push({
          title: '解题准确率偏低',
          description: '需要加强基础知识的理解和应用',
          severity: 'high',
          impact: '影响整体学习效果',
        });
      }

      if (userData.consistency < 0.5) {
        weaknesses.push({
          title: '学习缺乏规律性',
          description: '学习时间安排不够合理，需要建立学习计划',
          severity: 'medium',
          impact: '影响知识积累效率',
        });
      }

      if (userData.focusTime < 20) {
        weaknesses.push({
          title: '学习专注度不足',
          description: '单次学习时间较短，容易分心',
          severity: 'medium',
          impact: '影响深度学习效果',
        });
      }

      return weaknesses;
    },

    /**
     * 生成改进建议
     */
    generateRecommendations(userData, weaknesses) {
      const recommendations = [];

      weaknesses.forEach(weakness => {
        switch (weakness.title) {
          case '解题准确率偏低':
            recommendations.push({
              category: '基础强化',
              title: '夯实基础知识',
              content: '建议重点复习基础概念，多做基础练习题',
              priority: 'high',
              timeframe: '2-3周',
            });
            break;
          case '学习缺乏规律性':
            recommendations.push({
              category: '习惯养成',
              title: '制定学习计划',
              content: '每日固定时间学习，建立学习打卡习惯',
              priority: 'high',
              timeframe: '1-2周',
            });
            break;
          case '学习专注度不足':
            recommendations.push({
              category: '效率提升',
              title: '提高专注力',
              content: '使用番茄工作法，逐步延长单次学习时间',
              priority: 'medium',
              timeframe: '3-4周',
            });
            break;
        }
      });

      return recommendations;
    },

    /**
     * 制定改进计划
     */
    createImprovementPlan(weaknesses, recommendations) {
      const plan = [];
      
      // 按优先级排序建议
      const sortedRecommendations = recommendations.sort((a, b) => {
        const priorityOrder = { high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      });

      sortedRecommendations.forEach((rec, index) => {
        plan.push({
          step: index + 1,
          title: rec.title,
          description: rec.content,
          timeframe: rec.timeframe,
          priority: rec.priority,
          category: rec.category,
          completed: false,
        });
      });

      return plan;
    },

    /**
     * 分析学习风格
     */
    analyzeLearningStyle(userData) {
      // 基于用户行为数据推断学习风格
      let styleType = 'balanced';
      let description = '平衡型学习者';
      let characteristics = ['适应性强', '学习方式多样'];
      let suggestions = ['继续保持多样化的学习方式'];

      if (userData.visualPreference > 0.7) {
        styleType = 'visual';
        description = '视觉型学习者';
        characteristics = ['喜欢图表和图像', '空间思维能力强'];
        suggestions = ['多使用思维导图', '观看教学视频', '制作图表总结'];
      } else if (userData.auditoryPreference > 0.7) {
        styleType = 'auditory';
        description = '听觉型学习者';
        characteristics = ['善于听讲和讨论', '语言表达能力强'];
        suggestions = ['参与课堂讨论', '录音回顾重点', '大声朗读'];
      } else if (userData.kineticPreference > 0.7) {
        styleType = 'kinetic';
        description = '动觉型学习者';
        characteristics = ['喜欢动手操作', '实践能力强'];
        suggestions = ['多做实验和练习', '制作模型', '实地考察'];
      }

      this.setData({
        learningStyle: {
          type: styleType,
          description,
          characteristics,
          suggestions,
        }
      });
    },

    /**
     * 分析知识点掌握情况
     */
    analyzeKnowledgeMastery(userData) {
      const knowledgePoints = userData.knowledgePoints || [];
      const totalPoints = knowledgePoints.length;
      const masteredPoints = knowledgePoints.filter(point => point.mastery > 0.7).length;
      const masteryRate = totalPoints > 0 ? (masteredPoints / totalPoints) * 100 : 0;
      const weakPoints = knowledgePoints
        .filter(point => point.mastery < 0.6)
        .sort((a, b) => a.mastery - b.mastery)
        .slice(0, 5);

      this.setData({
        knowledgeMastery: {
          totalPoints,
          masteredPoints,
          masteryRate: Math.round(masteryRate),
          weakPoints,
        }
      });
    },

    /**
     * 分析学习行为模式
     */
    analyzeBehaviorPatterns(userData) {
      const behavior = userData.behavior || {};
      
      this.setData({
        behaviorAnalysis: {
          studyFrequency: this.getFrequencyDescription(behavior.frequency),
          sessionDuration: behavior.avgSessionDuration || 0,
          focusTime: this.getFocusDescription(behavior.avgSessionDuration),
          preferredTime: this.getPreferredTimeDescription(behavior.mostActiveHour),
          activePatterns: behavior.patterns || [],
        }
      });
    },

    /**
     * 分析进步趋势
     */
    analyzeProgressTrend(userData) {
      const trend = userData.trend || {};
      
      this.setData({
        progressTrend: {
          direction: trend.direction || 'stable',
          change: trend.change || 0,
          timeframe: trend.timeframe || '最近30天',
          keyMetrics: trend.metrics || [],
        }
      });
    },

    /**
     * 设置建议优先级
     */
    setPriorities() {
      const { weaknesses, recommendations } = this.data.diagnosis;
      
      const priorities = recommendations
        .filter(rec => rec.priority === 'high')
        .slice(0, 3)
        .map((rec, index) => ({
          rank: index + 1,
          title: rec.title,
          description: rec.content,
          urgency: rec.priority,
        }));

      this.setData({ priorities });
    },

    // 辅助方法
    getFrequencyDescription(frequency) {
      if (frequency >= 0.8) return '很规律';
      if (frequency >= 0.6) return '比较规律';
      if (frequency >= 0.4) return '一般';
      return '不够规律';
    },

    getFocusDescription(duration) {
      if (duration >= 45) return '专注度很好';
      if (duration >= 30) return '专注度良好';
      if (duration >= 15) return '专注度一般';
      return '专注度待提高';
    },

    getPreferredTimeDescription(hour) {
      if (hour >= 6 && hour < 12) return '上午';
      if (hour >= 12 && hour < 18) return '下午';
      if (hour >= 18 && hour < 24) return '晚上';
      return '深夜';
    },

    /**
     * 刷新诊断数据
     */
    refreshDiagnosis() {
      this.generateDiagnosis();
      this.triggerEvent('refresh');
    },

    /**
     * 查看详细建议
     */
    viewDetailedSuggestions() {
      this.triggerEvent('viewdetails', {
        recommendations: this.data.diagnosis.recommendations,
        plan: this.data.diagnosis.improvementPlan,
      });
    },

    /**
     * 开始改进计划
     */
    startImprovementPlan() {
      this.triggerEvent('startplan', {
        plan: this.data.diagnosis.improvementPlan,
      });
    },
  },
});