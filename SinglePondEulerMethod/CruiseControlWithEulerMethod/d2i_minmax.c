//Compile with gcc -rdynamic -O3 -c -Wall -Werror -fpic d2i_minmax.c -o libd2i_minmax.o ; gcc -rdynamic -shared -o libd2i_minmax.so libd2i_minmax.o

int cei(double x)
{
	if (x<0)
	{
		return (int)x;
	}
	else
	{
		int y = (int)x;
		return y + 1;
	}
}

int flo(double x)
{
	if (x>=0)
	{
		return (int)x;
	}
	else
	{
		int y = (int)x;
		return y - 1;
	}
}
