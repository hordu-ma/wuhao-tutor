<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h1 class="register-title">加入五好伴学</h1>
        <p class="register-subtitle">开启您的智能学习之旅</p>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="registerRules"
        class="register-form"
        size="large"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="registerForm.username"
            placeholder="用户名"
            prefix-icon="User"
            clearable
          />
        </el-form-item>

        <el-form-item prop="email">
          <el-input
            v-model="registerForm.email"
            placeholder="邮箱地址"
            prefix-icon="Message"
            clearable
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <el-form-item prop="role">
          <el-select
            v-model="registerForm.role"
            placeholder="选择身份"
            prefix-icon="Avatar"
            style="width: 100%"
          >
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
          </el-select>
        </el-form-item>

        <el-form-item prop="agreement">
          <el-checkbox v-model="registerForm.agreement">
            我已阅读并同意
            <el-link type="primary" @click="showTerms">《用户协议》</el-link>
            和
            <el-link type="primary" @click="showPrivacy">《隐私政策》</el-link>
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            class="register-button"
            :loading="registerLoading"
            @click="handleRegister"
          >
            {{ registerLoading ? "注册中..." : "立即注册" }}
          </el-button>
        </el-form-item>

        <el-form-item>
          <div class="login-link">
            已有账号？
            <el-link type="primary" @click="$router.push('/login')">
              立即登录
            </el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 服务条款对话框 -->
    <el-dialog
      v-model="showTermsDialog"
      title="用户服务协议"
      width="60%"
      center
    >
      <div class="terms-content">
        <h3>1. 服务条款的接受</h3>
        <p>
          欢迎使用五好伴学智能学习平台。使用本服务即表示您同意遵守以下条款。
        </p>

        <h3>2. 服务说明</h3>
        <p>五好伴学提供智能学习辅导、作业批改、学习问答等教育服务。</p>

        <h3>3. 用户责任</h3>
        <p>用户应提供真实、准确的注册信息，并承诺合理使用本平台服务。</p>

        <h3>4. 知识产权</h3>
        <p>平台内容受知识产权法保护，未经授权不得复制、传播或商业使用。</p>
      </div>
      <template #footer>
        <el-button @click="showTermsDialog = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 隐私政策对话框 -->
    <el-dialog
      v-model="showPrivacyDialog"
      title="隐私保护政策"
      width="60%"
      center
    >
      <div class="privacy-content">
        <h3>1. 信息收集</h3>
        <p>我们收集必要的用户信息以提供优质的教育服务。</p>

        <h3>2. 信息使用</h3>
        <p>用户信息仅用于提供学习服务，不会用于其他商业目的。</p>

        <h3>3. 信息保护</h3>
        <p>我们采用行业标准的安全措施保护用户信息。</p>

        <h3>4. 信息共享</h3>
        <p>除法律要求外，我们不会向第三方分享用户个人信息。</p>
      </div>
      <template #footer>
        <el-button @click="showPrivacyDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { ElMessage, ElNotification } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";

const router = useRouter();
const authStore = useAuthStore();

// 表单引用
const registerFormRef = ref<FormInstance>();

// 注册表单数据
const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  role: "student",
  agreement: false,
});

// 注册加载状态
const registerLoading = ref(false);

// 对话框显示状态
const showTermsDialog = ref(false);
const showPrivacyDialog = ref(false);

// 自定义验证器
const validatePassword = (_rule: any, value: any, callback: any) => {
  if (value === "") {
    callback(new Error("请输入密码"));
  } else if (value.length < 6) {
    callback(new Error("密码长度不能少于6位"));
  } else if (!/(?=.*[a-zA-Z])(?=.*\d)/.test(value)) {
    callback(new Error("密码必须包含字母和数字"));
  } else {
    // 如果确认密码已填写，需要重新验证
    if (registerForm.confirmPassword !== "") {
      registerFormRef.value?.validateField("confirmPassword");
    }
    callback();
  }
};

const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (value === "") {
    callback(new Error("请确认密码"));
  } else if (value !== registerForm.password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const validateEmail = (_rule: any, value: any, callback: any) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (value === "") {
    callback(new Error("请输入邮箱地址"));
  } else if (!emailRegex.test(value)) {
    callback(new Error("请输入正确的邮箱格式"));
  } else {
    callback();
  }
};

// 表单验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "用户名长度为3-20个字符", trigger: "blur" },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: "用户名只能包含字母、数字和下划线",
      trigger: "blur",
    },
  ],
  email: [{ validator: validateEmail, trigger: "blur" }],
  password: [{ validator: validatePassword, trigger: "blur" }],
  confirmPassword: [{ validator: validateConfirmPassword, trigger: "blur" }],
  role: [{ required: true, message: "请选择身份", trigger: "change" }],
  agreement: [
    {
      validator: (_rule: any, value: any, callback: any) => {
        if (!value) {
          callback(new Error("请阅读并同意用户协议和隐私政策"));
        } else {
          callback();
        }
      },
      trigger: "change",
    },
  ],
};

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return;

  try {
    // 表单验证
    const valid = await registerFormRef.value.validate();
    if (!valid) return;

    registerLoading.value = true;

    // 准备注册数据
    const registerData = {
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password,
      confirm_password: registerForm.confirmPassword,
      role: registerForm.role,
    };

    // 调用注册接口
    const success = await authStore.register(registerData);

    if (success) {
      ElNotification({
        title: "注册成功",
        message: "账号创建成功，请登录使用！",
        type: "success",
        duration: 4000,
      });

      // 跳转到登录页
      await router.push("/login");
    } else {
      ElMessage.error("注册失败，请检查输入信息");
    }
  } catch (error) {
    console.error("Register error:", error);
    ElMessage.error("注册过程中发生错误，请稍后重试");
  } finally {
    registerLoading.value = false;
  }
};

// 显示服务条款
const showTerms = () => {
  showTermsDialog.value = true;
};

// 显示隐私政策
const showPrivacy = () => {
  showPrivacyDialog.value = true;
};
</script>

<style lang="scss" scoped>
.register-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image:
      radial-gradient(
        circle at 20% 50%,
        rgba(120, 119, 198, 0.3) 0%,
        transparent 50%
      ),
      radial-gradient(
        circle at 80% 20%,
        rgba(255, 119, 198, 0.3) 0%,
        transparent 50%
      ),
      radial-gradient(
        circle at 40% 80%,
        rgba(120, 219, 255, 0.3) 0%,
        transparent 50%
      );
    pointer-events: none;
  }
}

.register-card {
  width: 100%;
  max-width: 460px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 40px 32px;
  position: relative;
  z-index: 1;
}

.register-header {
  text-align: center;
  margin-bottom: 32px;

  .register-title {
    font-size: 32px;
    font-weight: 700;
    color: #2c3e50;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .register-subtitle {
    font-size: 16px;
    color: #7f8c8d;
    margin: 0;
    font-weight: 400;
  }
}

.register-form {
  .el-form-item {
    margin-bottom: 20px;

    :deep(.el-input__wrapper) {
      border-radius: 8px;
      box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.1);
      transition: all 0.3s ease;

      &:hover {
        box-shadow: 0 0 0 1px var(--el-color-primary);
      }
    }

    :deep(.el-input__inner) {
      height: 48px;
      font-size: 16px;
    }

    :deep(.el-select) {
      width: 100%;

      .el-input__wrapper {
        height: 48px;
      }
    }
  }

  .el-checkbox {
    :deep(.el-checkbox__label) {
      color: #666;
      font-size: 14px;
      line-height: 1.5;
    }
  }
}

.register-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
  }

  &:active {
    transform: translateY(0);
  }

  &.is-loading {
    &:hover {
      transform: none;
      box-shadow: none;
    }
  }
}

.login-link {
  text-align: center;
  color: #666;
  font-size: 14px;

  .el-link {
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

// 对话框内容样式
.terms-content,
.privacy-content {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 10px;

  h3 {
    color: var(--el-color-primary);
    font-size: 16px;
    margin: 20px 0 10px 0;

    &:first-child {
      margin-top: 0;
    }
  }

  p {
    color: var(--el-text-color-regular);
    font-size: 14px;
    line-height: 1.6;
    margin: 0 0 15px 0;
  }
}

// 响应式设计
@media (max-width: 480px) {
  .register-container {
    padding: 16px;
  }

  .register-card {
    padding: 32px 24px;
  }

  .register-header .register-title {
    font-size: 28px;
  }

  .register-form .el-form-item :deep(.el-input__inner) {
    height: 44px;
    font-size: 15px;
  }

  .register-button {
    height: 44px;
    font-size: 15px;
  }

  :deep(.el-dialog) {
    width: 90% !important;
    margin: 5vh auto;
  }
}

// 动画效果
.register-card {
  animation: slideInUp 0.6s ease-out;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

// 暗色模式适配
.dark {
  .register-card {
    background: rgba(31, 41, 55, 0.95);
    border: 1px solid rgba(75, 85, 99, 0.2);

    .register-title {
      color: #f9fafb;
    }

    .register-subtitle {
      color: #9ca3af;
    }

    .register-form .el-checkbox :deep(.el-checkbox__label) {
      color: #d1d5db;
    }

    .login-link {
      color: #9ca3af;
    }
  }
}
</style>
