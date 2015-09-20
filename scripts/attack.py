#!/usr/bin/env python
import time
import sys
import argparse
import itertools
import string

EPSILON = 0.00001
ITERATIONS = 1000000
LENGTH = 10
# UNIVERSE = 'abcdefghijklmnopqrstuvwxyz'
# string.ascii_letters string.ascii_lowercase string.ascii_uppercase string.digits string.punctuation string.printables
UNIVERSE = string.ascii_lowercase
# UNIVERSE = string.ascii_letters + string.punctuation
# UNIVERSE = string.ascii_letters
MAX_LETTER_ATTEMPTS = 5

# TODO: don't hardcode the length, but do a timing attack to guess it first


def compare1(a, b):
	# counter = 0
	initial = time.time()
	zipped = list(zip(a, b))
	for _ in range(ITERATIONS):
		for x, y in zipped:
			# counter += 1
			if x != y:
				break
	# print('counter: {}'.format(counter))
	total = time.time() - initial
	return total


def compare2(a, b):
	initial = time.time()
	for _ in range(ITERATIONS):
		if a == b:
			pass
	total = time.time() - initial
	return total


def compare3(a, b):
	initial = time.time()
	a = list(a)
	b = list(b)
	for _ in range(ITERATIONS):
		if a == b:
			pass
	total = time.time() - initial
	return total


def letter(i):
	# return chr(97+i)
	return UNIVERSE[i]


def percentage_increase(a, b):
	return 100*(a - b)/b


def confident(x):
	# can definitely be improved with some statistics
	# return True
	a = sorted(x, reverse=True)
	if a[0] < EPSILON or a[1] < EPSILON or a[2] < EPSILON:
		return False
	diff1 = percentage_increase(a[0], a[1])
	diff2 = percentage_increase(a[1], a[2])
	print('diff1: {}'.format(diff1))
	print('diff2: {}'.format(diff2))
	if diff2 < EPSILON and diff1 > 100:  # can be optimized more, especially if we look at the rest of the list
		return True
	# if diff1 < EPSILON or diff2 < EPSILON:
	# 	return False
	confidence = percentage_increase(diff1, diff2)
	# confidence is the rate of change of the time differences between the topmost value (compared to the second)
	# and the second value (compared to the third)
	print('confidence: {}'.format(confidence))
	if diff1 < 10:
		print('diff1 is too small...')
		return False
	if confidence > 25:  # arbitrary reasonable value
		# we can optimize this ratio depending on the length and the iteration
		# i.e. how early we expect the equality check to return (e.g. if 9th out of 10 characters, diff1 (or conf) should be around 10%)
		return True
	else:
		return False


def timing(pwd, skip=False):
	total_time = 0
	attempt = ''.join(['a' for x in range(LENGTH)])  # to avoid early exits in comparisons
	result = ''
	i = 0
	letter_attempts = 0
	failed = False

	while i < len(pwd):
		times = []
		for j in range(len(UNIVERSE)):
			tmp = list(attempt)
			a = "".join('{}{}{}'.format(result, letter(j), attempt[len(result):]))
			print('attempting {} (real is {})'.format(a, pwd), end=" ", flush=True)
			initial = time.time()
			compare1(a, pwd)
			# compare2(a, pwd)
			# compare3(a, pwd)
			elapsed = time.time() - initial
			times.append(elapsed)
			print ('{}s'.format(times[-1]))

		if confident(times):
			selected = letter(max(enumerate(times), key=lambda x: x[1])[0])
			print('\n'.join(map(str, sorted([(letter(n), x) for n, x in enumerate(times)], reverse=True, key=lambda x: x[1]))))
			result += selected
			print ('selected: {}, pwd is now: {} (real is: {})'.format(selected, result, pwd))
			total_time += sum(times)
			i += 1
			letter_attempts = 0
			if not pwd.startswith(result):
				if not failed:
					failed = True
					input("We were confident about a letter that was wrong ({} instead of {}).\n"
						"It's a good idea to review the confidence criteria. Press return to continue...".format(result[i-1], pwd[i-1]))
				else:
					input("We were confident about a letter that was wrong, even after failing.\n"
						"This should be fairly rare as all letters should roughly have the same timing at this point.")
			if not skip:
				input('press return to continue...')
		else:
			print("we're not confident enough, should probably try larger iterations...")
			print('\n'.join(map(str, sorted([(letter(n), x) for n, x in enumerate(times)], reverse=True, key=lambda x: x[1]))))
			print("we're not confident enough, we could try again, try larger iterations, or backtrack. (or improve our confidence function if our guess would have been correct)...")
			if failed:
				print("so far, we found: {} (real is: {})".format(result, pwd))
				print("This makes sense since we already failed, they should all have roughly the same timing")
			else:
				print("so far, we found: {} (real is: {}) - next should be: {}".format(result, pwd, pwd[i]))

			if letter_attempts < MAX_LETTER_ATTEMPTS -1:
				letter_attempts += 1
				prompt = 'press return to try again... '
				if letter_attempts > 1:
					prompt += 'tried this letter {} times (out of {})...'.format(letter_attempts, MAX_LETTER_ATTEMPTS)
				input(prompt)
			else:
				print("Aborting after failing to find character #{} ({}) after {} tries. We suspect we maybe went into a wrong path and should backtrack here.".format(i, pwd[i], MAX_LETTER_ATTEMPTS))
				remaining = len(pwd) - i
				if remaining <= 5:
					brute_force = input("Since there are only {} characters left, we could try to [inefficiently] brute force the rest of the pwd. Type 'no' to skip it... ".format(remaining))  # this doesn't really make a lot of sense, but ok
					# should also offer to brute force after backtracking once (ie on result[:-1])
					if not brute_force.lower() == 'no':
						start = time.time()
						brute_result = brute(pwd, result)
						total_time += time.time() - start
						if brute_result:
							print("Found {} with the timing attack and {} by bruteforce for a result of {} (real is: {})".format(result, brute_result, result + brute_result, pwd))
							result += brute_result
						else:
							print("Couldn't find anything by bruteforcing. Should have probably backtracked at least one step first.")
				break

	if result == pwd:
		print("success! Total time: {}".format(total_time))
	else:
		print('failed :( - Total time: {}'.format(total_time))


def brute(pwd, prefix=''):
	result = None
	start = time.time()
	length = len(pwd) - len(prefix)
	pwd_suffix = pwd[-length:]
	print(pwd_suffix)
	print("pwd is: {}, relevant suffix is: {} - prefix is: {}".format(pwd, pwd_suffix, prefix))

	a = (''.join(x) for x in itertools.product(UNIVERSE, repeat=length))
	for x in a:
		if x == pwd_suffix:
			if pwd == prefix + x:
				print('pwd is: {}'.format(prefix + x))
				result = x
				break

	elapsed = time.time() - start
	print('Brute forcing {} characters took {}s'.format(length, elapsed))
	return result


def valid_pwd(pwd):
	if len(pwd) != LENGTH:
		print('length should be {} (instead of: {})'.format(LENGTH, len(pwd)))
		return False

	for x in pwd:
		if x not in UNIVERSE:
			print('Invalid character: {} - Must be in "{}"'.format(x, UNIVERSE))
			return False

	return True


def main():
	# parser = argparse.ArgumentParser(description="")
	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--skip-pause", help="skips asking for the return key at each iteration", action='store_true')
	args = parser.parse_args()

	pwd = input('password? ')
	while not valid_pwd(pwd):
		pwd = input('password? ')

	timing(pwd, skip=args.skip_pause)


if __name__ == '__main__':
	main()
