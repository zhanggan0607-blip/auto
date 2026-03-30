/**
 * Vue XSS 防护指令和过滤器
 * @module directives/xss
 */
import { sanitizeHtml, sanitizeUserInput } from '@/utils/xss';

/**
 * Vue 3 指令：v-xss-html
 * 用于显示富文本内容，自动过滤XSS风险
 * 用法: <div v-xss-html="content"></div>
 */
export const xssHtmlDirective = {
    mounted(el, binding) {
        if (binding.value) {
            el.innerHTML = sanitizeHtml(binding.value);
        } else {
            el.innerHTML = '';
        }
    },
    updated(el, binding) {
        if (binding.value !== binding.oldValue) {
            if (binding.value) {
                el.innerHTML = sanitizeHtml(binding.value);
            } else {
                el.innerHTML = '';
            }
        }
    }
};

/**
 * Vue 3 指令：v-xss
 * 用于普通文本插值，自动过滤HTML标签
 * 用法: <span v-xss="text"></span>
 */
export const xssDirective = {
    mounted(el, binding) {
        if (binding.value) {
            el.textContent = binding.value;
        } else {
            el.textContent = '';
        }
    },
    updated(el, binding) {
        if (binding.value !== binding.oldValue) {
            el.textContent = binding.value || '';
        }
    }
};

/**
 * Vue 3 指令：v-safe-html
 * 信任的HTML内容显示，仅移除脚本标签
 * 用法: <div v-safe-html="trustedContent"></div>
 */
export const safeHtmlDirective = {
    mounted(el, binding) {
        if (binding.value) {
            el.innerHTML = binding.value.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        } else {
            el.innerHTML = '';
        }
    },
    updated(el, binding) {
        if (binding.value !== binding.oldValue) {
            if (binding.value) {
                el.innerHTML = binding.value.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
            } else {
                el.innerHTML = '';
            }
        }
    }
};

/**
 * 过滤富文本编辑器内容（用于提交前）
 * @param {string} content - 编辑器内容
 * @returns {string} 过滤后的内容
 */
export function filterEditorContent(content) {
    if (!content) return '';

    let result = content;

    result = result.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');

    result = result.replace(/\son\w+\s*=\s*["'][^"']*["']/gi, '');

    result = result.replace(/javascript\s*:/gi, '');

    result = result.replace(/data\s*:/gi, '');

    return result;
}

/**
 * 注册全局指令
 * @param {import('vue').App} app - Vue应用实例
 */
export function registerXssDirectives(app) {
    app.directive('xss-html', xssHtmlDirective);
    app.directive('xss', xssDirective);
    app.directive('safe-html', safeHtmlDirective);
}

export default {
    xssHtmlDirective,
    xssDirective,
    safeHtmlDirective,
    filterEditorContent,
    registerXssDirectives
};