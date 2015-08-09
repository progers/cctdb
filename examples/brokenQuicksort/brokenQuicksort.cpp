// A broken quicksort program (there is a bug).
//
// This program parses a list of numbers and then sorts them, printing the
// result to standard out.
//
// Usage: ./brokenQuicksort 1 4 3 9 1
//        1 1 3 4 9

#include <stdio.h>
#include <cstdlib>

void swap(int* numbers, int a, int b) {
    int temp = numbers[a];
    numbers[a] = numbers[b];
    numbers[b] = temp;
}

int partition(int* numbers, int a, int b) {
    int pivot = numbers[b];
    while (a < b) {
        while (numbers[a] < pivot)
            a++;
        while (numbers[b] > pivot)
            b--;
        if (numbers[a] == numbers[b])
            a++;
        else if (a < b)
            swap(numbers, a, b);
    }
    return b;
}

void quicksort(int* numbers, int a, int b) {
    if (a < b) {
        int m = partition(numbers, a, b);
        quicksort(numbers, a, m - 1);
        quicksort(numbers, m + 1, b);
        if (numbers[a] == 5) // WARNING: THIS IS A BUG!
            swap(numbers, a, b);
    }
}

void sort(int* numbers, int count) {
    quicksort(numbers, 0, count);
}

int main(int argc, char *argv[]) {
    int numArgs = argc - 1;
    if (numArgs < 1) {
        fprintf(stderr, "Run with a list of numbers to sort them.\n");
        return 1;
    }

    // Read in the numbers from the arguments.
    int* numbers = new int[numArgs];
    for (int argIndex = 0; argIndex < numArgs; argIndex++)
        numbers[argIndex] = atoi(argv[argIndex + 1]);

    sort(numbers, numArgs - 1);

    // Write our output.
    for (int argIndex = 0; argIndex < numArgs; argIndex++)
        fprintf(stdout, "%d ", numbers[argIndex]);
    fprintf(stdout, "\n");

    delete[] numbers;
    return 0;
}
