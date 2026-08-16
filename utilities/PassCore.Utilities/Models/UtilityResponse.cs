namespace PassCore.Utilities.Models;

public sealed class UtilityResponse{
    public bool Success { get; set; }
    public string? Error { get; set; }
    public object? Data { get; set; }

    public static UtilityResponse Ok(object? data = null){
        return new UtilityResponse{
            Success = true,
            Data = data
        };
    }
    public static UtilityResponse Fail(string error){
        return new UtilityResponse{
            Success = false,
            Error = error
        };
    }
}