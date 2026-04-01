from app.tasks import load_scenarios, get_task_metadata, list_all_tasks
from app.grader import Grader
from app.memory import MemoryEngine

# Test task loading
for tid in ['easy', 'medium', 'hard', 'expert']:
    meta = get_task_metadata(tid)
    print(tid + ': ' + str(meta['num_scenarios']) + ' scenarios | ' + str(meta['max_turns']) + ' max turns')

# Test task list
tasks = list_all_tasks()
print('Total tasks: ' + str(len(tasks)))
print('tasks OK')