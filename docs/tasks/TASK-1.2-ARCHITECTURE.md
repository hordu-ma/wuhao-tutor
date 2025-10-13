# Task 1.2 Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (Future)                      │
│                   /api/v1/mistakes/*                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                            │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           MistakeService (15 methods)                │   │
│  │                                                       │   │
│  │  • CRUD: create, read, update, delete                │   │
│  │  • Review: get_today_tasks, complete_review         │   │
│  │  • Stats: get_statistics, get_mastery_progress      │   │
│  │  • History: get_review_history                       │   │
│  │  • AI: analyze_mistake_with_ai                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                              ↓                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │      SpacedRepetitionAlgorithm                       │   │
│  │                                                       │   │
│  │  • calculate_next_review()                           │   │
│  │  • calculate_mastery_level()                         │   │
│  │  • is_mastered()                                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Repository Layer                           │
│                                                              │
│  ┌────────────────────┐      ┌─────────────────────────┐   │
│  │ MistakeRepository  │      │ MistakeReviewRepository │   │
│  │    (12 methods)    │      │      (8 methods)        │   │
│  │                    │      │                         │   │
│  │ • find_by_user     │      │ • find_by_mistake       │   │
│  │ • find_due_review  │      │ • get_latest_review     │   │
│  │ • find_by_kp       │      │ • calc_avg_mastery      │   │
│  │ • get_statistics   │      │ • get_review_streak     │   │
│  │ • search_mistakes  │      │ • get_accuracy          │   │
│  │ • ...              │      │ • ...                   │   │
│  └────────────────────┘      └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Database Layer                           │
│                                                              │
│  ┌────────────────────┐      ┌─────────────────────────┐   │
│  │  mistake_records   │      │   mistake_reviews       │   │
│  │                    │      │                         │   │
│  │ • id (UUID)        │      │ • id (UUID)             │   │
│  │ • user_id          │◄─────┤ • mistake_id (FK)       │   │
│  │ • subject          │      │ • user_id (FK)          │   │
│  │ • mastery_status   │      │ • review_result         │   │
│  │ • review_count     │      │ • mastery_level         │   │
│  │ • next_review_at   │      │ • next_review_date      │   │
│  │ • knowledge_points │      │ • confidence_level      │   │
│  └────────────────────┘      └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow: Complete Review Workflow

```
User submits review
       ↓
MistakeService.complete_review()
       ↓
┌──────────────────────────────────────────────────────┐
│ 1. Validate ownership                                 │
│    └─→ MistakeRepository.get_by_id()                 │
├──────────────────────────────────────────────────────┤
│ 2. Create review record                              │
│    └─→ MistakeReviewRepository.create()              │
├──────────────────────────────────────────────────────┤
│ 3. Calculate mastery                                 │
│    ├─→ MistakeReviewRepository.find_by_mistake()     │
│    └─→ Algorithm.calculate_mastery_level()           │
│         (weighted avg of last 5 reviews)             │
├──────────────────────────────────────────────────────┤
│ 4. Calculate next review time                        │
│    └─→ Algorithm.calculate_next_review()             │
│         • Check review_result (correct/incorrect)    │
│         • Get base interval from Ebbinghaus          │
│         • Adjust by mastery (×0.8 or ×1.2)          │
├──────────────────────────────────────────────────────┤
│ 5. Update mistake record                             │
│    └─→ MistakeRepository.update()                    │
│         • review_count++                             │
│         • next_review_at = calculated_date           │
│         • mastery_status (if mastered)               │
├──────────────────────────────────────────────────────┤
│ 6. Check mastery threshold                           │
│    └─→ Algorithm.is_mastered()                       │
│         • mastery_level ≥ 0.9?                       │
│         • consecutive_correct ≥ 3?                   │
└──────────────────────────────────────────────────────┘
       ↓
Return ReviewCompleteResponse
```

## Ebbinghaus Algorithm Flow

```
Input: review_count, review_result, current_mastery, last_review_date
       ↓
┌──────────────────────────────────────────────┐
│ Step 1: Determine base interval              │
│                                              │
│ if review_result == "incorrect":             │
│     interval = INTERVALS[0]  # 1 day         │
│                                              │
│ elif review_result == "partial":             │
│     interval = INTERVALS[review_count]       │
│     # Repeat current interval                │
│                                              │
│ else:  # correct                             │
│     interval = INTERVALS[review_count + 1]   │
│     # Move to next interval                  │
└──────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────┐
│ Step 2: Adjust by mastery level              │
│                                              │
│ if current_mastery < 0.5:                    │
│     interval = int(interval * 0.8)           │
│     # Low mastery → shorter interval         │
│                                              │
│ elif current_mastery > 0.8:                  │
│     interval = int(interval * 1.2)           │
│     # High mastery → longer interval         │
└──────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────┐
│ Step 3: Calculate next review date           │
│                                              │
│ next_review = last_review_date +             │
│               timedelta(days=interval)       │
└──────────────────────────────────────────────┘
       ↓
Output: (next_review_date, interval_days)
```

## Mastery Calculation Flow

```
Input: review_history (list of MistakeReview)
       ↓
┌──────────────────────────────────────────────┐
│ Step 1: Get last 5 reviews                   │
│                                              │
│ recent = review_history[:5]                  │
└──────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────┐
│ Step 2: Apply weighted average               │
│                                              │
│ weights = [0.4, 0.3, 0.15, 0.1, 0.05]       │
│ scores = {                                   │
│     "correct": 1.0,                          │
│     "partial": 0.5,                          │
│     "incorrect": 0.0                         │
│ }                                            │
│                                              │
│ total = 0                                    │
│ for i, review in enumerate(recent):          │
│     score = scores[review.review_result]     │
│     weight = weights[i]                      │
│     total += score * weight                  │
└──────────────────────────────────────────────┘
       ↓
┌──────────────────────────────────────────────┐
│ Step 3: Round to 2 decimal places            │
│                                              │
│ mastery = round(total, 2)                    │
└──────────────────────────────────────────────┘
       ↓
Output: mastery_level (0.0 - 1.0)
```

## Example Scenarios

### Scenario 1: First Review - Correct Answer
```
Input:
  review_count = 0
  review_result = "correct"
  current_mastery = 0.4 (calculated from this review)
  
Flow:
  1. Base interval = INTERVALS[0+1] = INTERVALS[1] = 2 days
  2. Mastery < 0.5 → 2 * 0.8 = 1.6 → 1 day
  3. Next review = today + 1 day
  
Output: (tomorrow, 1 day)
```

### Scenario 2: Third Review - Incorrect Answer
```
Input:
  review_count = 2
  review_result = "incorrect"
  current_mastery = 0.3
  
Flow:
  1. Base interval = INTERVALS[0] = 1 day (reset!)
  2. Mastery < 0.5 → 1 * 0.8 = 0.8 → 1 day (min)
  3. Next review = today + 1 day
  
Output: (tomorrow, 1 day)
```

### Scenario 3: Fifth Review - High Mastery
```
Input:
  review_count = 4
  review_result = "correct"
  current_mastery = 0.9
  
Flow:
  1. Base interval = INTERVALS[4+1] = INTERVALS[5] = 30 days
  2. Mastery > 0.8 → 30 * 1.2 = 36 days
  3. Next review = today + 36 days
  4. Check mastery: 0.9 ≥ 0.9? Yes
  5. Check consecutive: Need to verify ≥ 3
  6. If yes → mastery_status = "mastered"
  
Output: (36 days later, 36 days, possibly mastered)
```

## Schema Relationships

```
CreateMistakeRequest
       ↓
MistakeService.create_mistake()
       ↓
MistakeRecord (DB)
       ↓
MistakeListItem / MistakeDetailResponse
       ↓
API Response

ReviewCompleteRequest
       ↓
MistakeService.complete_review()
       ↓
MistakeReview (DB) + Update MistakeRecord
       ↓
ReviewCompleteResponse
       ↓
API Response
```

## Test Coverage Map

```
SpacedRepetitionAlgorithm
├─ calculate_next_review
│  ├─ ✅ Correct progression (7 cases)
│  ├─ ✅ Incorrect reset (4 cases)
│  ├─ ✅ Partial repeat (4 cases)
│  ├─ ✅ Low mastery adjustment
│  └─ ✅ High mastery adjustment
├─ calculate_mastery_level
│  ├─ ✅ No history
│  ├─ ✅ Single review
│  ├─ ✅ Weighted average (5 reviews)
│  └─ ✅ More than 5 reviews
└─ is_mastered
   └─ ✅ 6 threshold scenarios

MistakeService
├─ ✅ Initialization
├─ ✅ create_mistake
├─ ✅ get_mistake_list
└─ ✅ get_statistics

Total: 36+ tests, 100% algorithm coverage
```

## Key Implementation Patterns

### 1. Type Safety
```python
async def complete_review(
    self,
    mistake_id: UUID,
    user_id: UUID,
    request: ReviewCompleteRequest
) -> ReviewCompleteResponse:
    ...
```

### 2. Error Handling
```python
if not mistake or str(mistake.user_id) != str(user_id):
    raise NotFoundError(f"错题 {mistake_id} 不存在")
```

### 3. Repository Pattern
```python
class MistakeRepository(BaseRepository[MistakeRecord]):
    # Inherits: create, update, delete, get_by_id
    # Adds: find_by_user, find_due_for_review, etc.
```

### 4. Algorithm Encapsulation
```python
# Pure logic, no database dependencies
class SpacedRepetitionAlgorithm:
    @staticmethod
    def calculate_next_review(...) -> Tuple[datetime, int]:
        ...
```

## Files Overview

```
src/
├── repositories/
│   ├── mistake_repository.py          (430 lines)
│   └── mistake_review_repository.py   (260 lines)
├── services/
│   ├── algorithms/
│   │   └── spaced_repetition.py       (195 lines)
│   └── mistake_service.py             (350 lines)
└── schemas/
    └── mistake.py                     (+150 lines)

tests/
├── algorithms/
│   └── test_spaced_repetition.py      (220 lines)
├── repositories/
│   └── test_mistake_repository.py     (120 lines)
└── services/
    └── test_mistake_service.py        (100 lines)

Total: ~1,700 lines of code + tests
```
