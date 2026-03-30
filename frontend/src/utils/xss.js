/**
 * XSS 安全过滤工具
 * 防止跨站脚本攻击（XSS）
 * 安全改进：集成DOMPurify库，提供更全面的XSS防护
 * @module utils/xss
 */
import DOMPurify from 'dompurify';

/**
 * DOMPurify配置 - 仅允许安全标签
 */
const PURIFY_CONFIG = {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br', 'span', 'div', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'blockquote', 'code', 'pre'],
    ALLOWED_ATTR: ['href', 'title', 'class'],
    ALLOW_DATA_ATTR: false,
    FORBID_TAGS: ['style', 'script', 'iframe', 'object', 'embed', 'form', 'input', 'button', 'select', 'textarea', 'link', 'base', 'meta'],
    FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur', 'onchange', 'onsubmit'],
    KEEP_CONTENT: true,
    RETURN_TRUSTED_TYPE: false,
};

/**
 * HTML实体映射表
 */
const HTML_ENTITIES = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
    '`': '&#x60;',
    '=': '&#x3D'
};

/**
 * XSS过滤正则表达式
 */
const XSS_PATTERNS = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript\s*:/gi,
    /on\w+\s*=/gi,
    /<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>/gi,
    /<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>/gi,
    /<embed\b[^<]*(?:(?!<\/embed>)<[^<]*)*<\/embed>/gi,
    /<link\b[^<]*(?:(?!<\/link>)<[^<]*)*<\/link>/gi,
    /<base\b[^<]*(?:(?!<\/base>)<[^<]*)*<\/base>/gi,
    /<meta\b[^<]*(?:(?!<\/meta>)<[^<]*)*<\/meta>/gi,
    /expression\s*\(/gi,
    /url\s*\(/gi,
    /data\s*:/gi,
];

/**
 * 敏感属性列表
 */
const SENSITIVE_ATTRS = [
    'href', 'src', 'action', 'formaction', 'xlink:href', 'background', 'poster',
    'onload', 'onerror', 'onclick', 'onmouseover', 'onfocus', 'onblur', 'onchange',
    'onsubmit', 'onreset', 'onabort', 'onkeydown', 'onkeypress', 'onkeyup',
    'onmousedown', 'onmousemove', 'onmouseout', 'onmouseup', 'ondblclick',
    'ondrag', 'ondragend', 'ondragenter', 'ondragleave', 'ondragover', 'ondragstart',
    'ondrop', 'onscroll', 'onwheel', 'oncopy', 'oncut', 'onpaste'
];

/**
 * 转义HTML特殊字符
 * @param {string} text - 待转义文本
 * @returns {string} 转义后的文本
 */
export function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/[&<>"'`=/]/g, char => HTML_ENTITIES[char] || char);
}

/**
 * 解转义HTML
 * @param {string} text - 待解转义文本
 * @returns {string} 解转义后的文本
 */
export function unescapeHtml(text) {
    if (!text) return '';
    const entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"',
        '&#x27;': "'", '&#x2F;': '/', '&#x60;': '`', '&#x3D': '='
    };
    return text.replace(/&(?:amp|lt|gt|quot|#x27|#x2F|#x60|#x3D);/g, entity => entities[entity] || entity);
}

/**
 * 检查文本是否包含XSS风险
 * @param {string} text - 待检查文本
 * @returns {boolean} 是否安全
 */
export function containsXssRisk(text) {
    if (!text) return false;
    for (const pattern of XSS_PATTERNS) {
        if (pattern.test(text)) return true;
    }
    const lowerText = text.toLowerCase();
    if (lowerText.includes('script') && lowerText.includes('<')) return true;
    return false;
}

/**
 * 过滤XSS脚本标签
 * @param {string} text - 待过滤文本
 * @returns {string} 过滤后的文本
 */
export function stripScriptTags(text) {
    if (!text) return '';
    return text.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
}

/**
 * 过滤事件处理器属性
 * @param {string} text - 待过滤文本
 * @returns {string} 过滤后的文本
 */
export function stripEventHandlers(text) {
    if (!text) return '';
    let result = text;
    for (const attr of SENSITIVE_ATTRS) {
        const regex = new RegExp(`\\s*${attr}\\s*=\\s*["'][^"']*["']`, 'gi');
        result = result.replace(regex, '');
    }
    return result;
}

/**
 * 安全过滤HTML - 使用DOMPurify
 * @param {string} html - 待过滤HTML
 * @returns {string} 过滤后的HTML
 */
export function sanitizeHtml(html) {
    if (!html) return '';
    try {
        const cleaned = DOMPurify.sanitize(html, PURIFY_CONFIG);
        return cleaned;
    } catch (e) {
        console.warn('DOMPurify过滤失败，使用备用方案:', e);
        let result = html;
        result = stripScriptTags(result);
        result = stripEventHandlers(result);
        const dangerousTags = ['iframe', 'object', 'embed', 'link', 'base', 'meta', 'style', 'svg', 'math'];
        for (const tag of dangerousTags) {
            const regex = new RegExp(`<${tag}\\b[^<]*(?:(?!<\\/${tag}>)<[^<]*)*<\\/${tag}>`, 'gi');
            result = result.replace(regex, '');
        }
        return result;
    }
}

/**
 * 过滤危险URL
 * @param {string} url - 待过滤URL
 * @returns {string} 过滤后的URL
 */
export function sanitizeUrl(url) {
    if (!url) return '';
    const lowerUrl = url.toLowerCase().trim();
    if (lowerUrl.startsWith('javascript:') || lowerUrl.startsWith('data:') || lowerUrl.startsWith('vbscript:')) {
        return '';
    }
    return url;
}

/**
 * 对HTML属性值进行安全处理
 * @param {string} value - 属性值
 * @returns {string} 处理后的值
 */
export function sanitizeAttrValue(value) {
    if (!value) return '';
    let result = value;
    result = escapeHtml(result);
    result = sanitizeUrl(result);
    return result;
}

/**
 * 深度过滤对象中的XSS风险
 * @param {any} obj - 待过滤对象
 * @param {Array<string>} fields - 需要过滤的字段名
 * @returns {any} 过滤后的对象
 */
export function sanitizeObject(obj, fields = null) {
    if (!obj) return obj;
    if (typeof obj === 'string') return sanitizeHtml(obj);
    if (Array.isArray(obj)) return obj.map(item => sanitizeObject(item, fields));
    if (typeof obj === 'object') {
        const result = {};
        for (const key in obj) {
            if (Object.prototype.hasOwnProperty.call(obj, key)) {
                const value = obj[key];
                if (fields === null || fields.includes(key)) {
                    if (typeof value === 'string') result[key] = sanitizeHtml(value);
                    else result[key] = sanitizeObject(value, fields);
                } else {
                    result[key] = sanitizeObject(value, fields);
                }
            }
        }
        return result;
    }
    return obj;
}

/**
 * 过滤用户输入（用于搜索、评论等场景）
 * @param {string} input - 用户输入
 * @returns {string} 过滤后的输入
 */
export function sanitizeUserInput(input) {
    if (!input) return '';
    let result = input;
    result = escapeHtml(result);
    result = result.replace(/[<>'"`]/g, char => HTML_ENTITIES[char] || char);
    return result.trim();
}

/**
 * 验证并过滤请求体中的敏感数据
 * @param {Object} data - 请求数据
 * @returns {Object} 过滤后的数据
 */
export function sanitizeRequestData(data) {
    if (!data) return data;
    const sensitiveFields = [
        'password', 'oldPassword', 'newPassword', 'confirmPassword', 'token',
        'accessToken', 'refreshToken', 'apiKey', 'secretKey', 'creditCode',
        'bankAccount', 'idCard'
    ];
    const result = {};
    for (const key in data) {
        if (Object.prototype.hasOwnProperty.call(data, key)) {
            const value = data[key];
            if (sensitiveFields.includes(key)) {
                if (typeof value === 'string' && value.length > 0) result[key] = '***FILTERED***';
                else result[key] = value;
            } else if (typeof value === 'string') result[key] = sanitizeUserInput(value);
            else if (typeof value === 'object' && value !== null) result[key] = sanitizeRequestData(value);
            else result[key] = value;
        }
    }
    return result;
}

/**
 * 过滤响应数据中的敏感信息（用于日志记录）
 * @param {Object} data - 响应数据
 * @returns {Object} 过滤后的数据
 */
export function sanitizeResponseData(data) {
    if (!data) return data;
    const sensitiveFields = [
        'password', 'token', 'accessToken', 'refreshToken', 'apiKey', 'secretKey',
        'creditCode', 'bankAccount', 'idCard', 'phone', 'mobile', 'email', 'address', 'contactInfo'
    ];
    const result = {};
    for (const key in data) {
        if (Object.prototype.hasOwnProperty.call(data, key)) {
            const value = data[key];
            if (sensitiveFields.includes(key)) {
                if (typeof value === 'string' && value.length > 0) result[key] = maskSensitive(value);
                else result[key] = value;
            } else if (typeof value === 'string') result[key] = value;
            else if (Array.isArray(value)) result[key] = value.map(item => sanitizeResponseData(item));
            else if (typeof value === 'object' && value !== null) result[key] = sanitizeResponseData(value);
            else result[key] = value;
        }
    }
    return result;
}

/**
 * 遮蔽敏感信息
 * @param {string} value - 原始值
 * @param {number} visibleChars - 保留可见字符数
 * @returns {string} 遮蔽后的值
 */
export function maskSensitive(value, visibleChars = 4) {
    if (!value) return '';
    if (value.length <= visibleChars) return '*'.repeat(value.length);
    const start = value.slice(0, visibleChars);
    const end = value.slice(-visibleChars);
    const masked = '*'.repeat(Math.min(value.length - visibleChars * 2, 8));
    return `${start}${masked}${end}`;
}

export default {
    escapeHtml, unescapeHtml, containsXssRisk, stripScriptTags, stripEventHandlers,
    sanitizeHtml, sanitizeUrl, sanitizeAttrValue, sanitizeObject, sanitizeUserInput,
    sanitizeRequestData, sanitizeResponseData, maskSensitive
};
