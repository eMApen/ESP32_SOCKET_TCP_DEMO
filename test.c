#include <stdio.h>

int main(void) { 
	
    int xlen;
    xlen=1234567;
    // %04
    int a,b,d,e,f,g;
    char* clen = &xlen;
    
    printf("%d,%d,%c,%d,%d",xlen,&xlen,clen,&clen,clen);
}