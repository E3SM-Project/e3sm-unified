# Additional C++ command line flags
CXXFLAGS+=         -fPIC

# NetCDF C library arguments
NETCDF_ROOT=       $(NETCDF_C_PATH)
NETCDF_CXXFLAGS=   -I$(NETCDF_ROOT)/include
NETCDF_LIBRARIES=  -lnetcdf_c++ -lnetcdf
NETCDF_LDFLAGS=    -L$(NETCDF_ROOT)/lib
