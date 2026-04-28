#!/bin/sh
# Pre-commit hook for TypeScript type checking
# Install: Copy this file to .git/hooks/pre-commit or use husky

echo "Running TypeScript type check..."

cd "$(dirname "$0")/.."

# Check if vue-tsc is available
if ! command -v vue-tsc &> /dev/null; then
    echo "vue-tsc not found, skipping type check"
    exit 0
fi

# Run type check
npx vue-tsc --noEmit

if [ $? -ne 0 ]; then
    echo ""
    echo "Type check failed! Please fix type errors before committing."
    echo "To bypass this check temporarily, use: git commit --no-verify"
    exit 1
fi

echo "Type check passed!"
exit 0
